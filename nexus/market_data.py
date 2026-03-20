from __future__ import annotations

import asyncio
import contextlib
import json
import math
import random
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any

from config.settings import get_settings
from neural_os.event_bus import EventBus

try:
    import websockets
except ImportError:  # pragma: no cover
    websockets = None


class MarketDataClient:
    def __init__(self, event_bus: EventBus) -> None:
        self.settings = get_settings()
        self.event_bus = event_bus
        self.symbols = list(self.settings.bybit_symbols)
        self._task: asyncio.Task[None] | None = None
        self._running = False
        self._mode = 'bootstrap'
        self._rng = random.Random(self.settings.mock_market_seed)
        self._candles: dict[str, deque[dict[str, Any]]] = {symbol: deque(maxlen=self.settings.market_history_limit) for symbol in self.symbols}
        self._latest_tick: dict[str, Any] = {'symbol': self.symbols[0], 'price': 100.0, 'source': 'bootstrap', 'timestamp': datetime.now(timezone.utc).isoformat()}
        self._seed_initial_history()

    def _seed_initial_history(self) -> None:
        now = int(time.time())
        for offset, symbol in enumerate(self.symbols):
            base = 10 + offset * 2.5
            for index in range(220):
                t = now - (220 - index) * 60
                close = base + math.sin(index / 8 + offset) * 0.7 + index * 0.01
                candle = self._make_candle(symbol, float(close), t)
                self._candles[symbol].append(candle)

    def _make_candle(self, symbol: str, close: float, ts: int | None = None) -> dict[str, Any]:
        ts = ts or int(time.time())
        open_price = close * (1 - 0.001)
        high = max(open_price, close) * 1.002
        low = min(open_price, close) * 0.998
        return {'symbol': symbol, 'timestamp': ts, 'open': round(open_price, 6), 'high': round(high, 6), 'low': round(low, 6), 'close': round(close, 6), 'volume': round(abs(close) * 1000, 4), 'spread': 0.0015, 'funding_rate': 0.0005, 'source': self._mode}

    @property
    def latest_tick(self) -> dict[str, Any]:
        return self._latest_tick

    def candle_snapshot(self) -> dict[str, list[dict[str, Any]]]:
        return {symbol: list(candles) for symbol, candles in self._candles.items()}

    async def start(self) -> None:
        if self._task is None:
            self._running = True
            self._task = asyncio.create_task(self._run(), name='market-data')

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def start_once(self) -> None:
        await self._publish_mock_round()

    async def _run(self) -> None:
        while self._running:
            try:
                if websockets is None:
                    raise RuntimeError('websockets dependency unavailable')
                await self._consume_live_feed()
            except Exception:
                self._mode = 'mock'
                await self._publish_mock_round()
                await asyncio.sleep(1.0)

    async def _consume_live_feed(self) -> None:
        self._mode = 'live'
        async with websockets.connect(self.settings.bybit_ws_url, ping_interval=20, ping_timeout=20) as websocket:
            args = [f'kline.1.{symbol}' for symbol in self.symbols]
            await websocket.send(json.dumps({'op': 'subscribe', 'args': args}))
            while self._running:
                message = json.loads(await websocket.recv())
                topic = str(message.get('topic', ''))
                if not topic.startswith('kline.1.'):
                    continue
                symbol = topic.split('.')[-1]
                rows = message.get('data') or []
                if not rows:
                    continue
                raw = rows[0] if isinstance(rows, list) else rows
                candle = {'symbol': symbol, 'timestamp': int(raw.get('start', time.time())), 'open': float(raw.get('open', 0.0)), 'high': float(raw.get('high', 0.0)), 'low': float(raw.get('low', 0.0)), 'close': float(raw.get('close', 0.0)), 'volume': float(raw.get('volume', 0.0)), 'spread': 0.001, 'funding_rate': 0.0005, 'source': 'bybit'}
                await self._record_candle(symbol, candle)

    async def _publish_mock_round(self) -> None:
        for index, symbol in enumerate(self.symbols):
            last_close = float(self._candles[symbol][-1]['close']) if self._candles[symbol] else 10.0 + index
            drift = math.sin(time.time() / 30 + index) * 0.05
            noise = self._rng.uniform(-0.03, 0.03)
            close = max(0.1, last_close * (1 + drift * 0.001 + noise * 0.001))
            candle = self._make_candle(symbol, close)
            candle['source'] = 'mock'
            await self._record_candle(symbol, candle)

    async def _record_candle(self, symbol: str, candle: dict[str, Any]) -> None:
        self._candles[symbol].append(candle)
        self._latest_tick = {'symbol': symbol, 'price': candle['close'], 'source': candle['source'], 'timestamp': datetime.now(timezone.utc).isoformat(), 'spread': candle.get('spread', 0.0), 'funding_rate': candle.get('funding_rate', 0.0)}
        await self.event_bus.publish(f'nexus.candle.{symbol}', candle)

    def latest_candles(self, symbol: str, limit: int = 200) -> list[dict[str, Any]]:
        return list(self._candles.get(symbol, []))[-limit:]

    def flush_history(self, keep_last: int = 100) -> None:
        for symbol, candles in self._candles.items():
            trimmed = list(candles)[-keep_last:]
            self._candles[symbol] = deque(trimmed, maxlen=self.settings.market_history_limit)

    def health(self) -> dict[str, Any]:
        return {'status': 'ok', 'response_time_ms': 0.0, 'mode': self._mode, 'symbols': len(self.symbols), 'latest_symbol': self._latest_tick['symbol']}
