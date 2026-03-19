from __future__ import annotations

import asyncio
import contextlib
import json
import time
from dataclasses import asdict, dataclass
from typing import Any

try:
    import websockets
except Exception:  # pragma: no cover
    websockets = None

from config.settings import get_settings


@dataclass(slots=True)
class MarketSnapshot:
    symbol: str
    price: float
    turnover_24h: float
    funding_rate: float
    open_interest: float
    timestamp: float
    source: str


class BybitMarketDataClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._task: asyncio.Task[None] | None = None
        self._running = False
        self._latest: dict[str, MarketSnapshot] = {}

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._running = True
        self._task = asyncio.create_task(self._consume(), name='bybit-market-data')

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

    def latest(self) -> list[dict[str, Any]]:
        if self._latest:
            return [asdict(snapshot) for snapshot in self._latest.values()]
        return [self._fallback_snapshot(symbol) for symbol in self.settings.bybit_symbols]

    async def _consume(self) -> None:
        if websockets is None:
            self._apply_fallback()
            while self._running:
                await asyncio.sleep(5)
            return
        subscribe = {'op': 'subscribe', 'args': [f'tickers.{symbol}' for symbol in self.settings.bybit_symbols]}
        while self._running:
            try:
                async with websockets.connect(self.settings.bybit_ws_url, ping_interval=20, ping_timeout=20) as websocket:
                    await websocket.send(json.dumps(subscribe))
                    while self._running:
                        message = json.loads(await websocket.recv())
                        await self._handle_message(message)
            except Exception:
                self._apply_fallback()
                await asyncio.sleep(5)

    async def _handle_message(self, message: dict[str, Any]) -> None:
        topic = message.get('topic', '')
        if not topic.startswith('tickers.'):
            return
        payload = message.get('data') or {}
        symbol = payload.get('symbol', topic.split('.')[-1])
        snapshot = MarketSnapshot(
            symbol=symbol,
            price=float(payload.get('lastPrice') or 0.0),
            turnover_24h=float(payload.get('turnover24h') or 0.0),
            funding_rate=float(payload.get('fundingRate') or 0.0),
            open_interest=float(payload.get('openInterest') or 0.0),
            timestamp=time.time(),
            source='bybit',
        )
        self._latest[symbol] = snapshot

    def _apply_fallback(self) -> None:
        for symbol in self.settings.bybit_symbols:
            generated = self._fallback_snapshot(symbol)
            self._latest[symbol] = MarketSnapshot(**generated)

    def _fallback_snapshot(self, symbol: str) -> dict[str, Any]:
        seed = sum(ord(char) for char in symbol)
        return {
            'symbol': symbol,
            'price': round(seed / 10.0, 4),
            'turnover_24h': float(seed * 1000),
            'funding_rate': round((seed % 7) / 10000, 6),
            'open_interest': float(seed * 100),
            'timestamp': time.time(),
            'source': 'fallback',
        }
