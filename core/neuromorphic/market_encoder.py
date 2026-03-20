from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, AsyncIterator

from neural_os.event_bus import EventBus


class PatternType(str, Enum):
    ACCUMULATION = 'ACCUMULATION'
    DISTRIBUTION = 'DISTRIBUTION'
    BREAKOUT = 'BREAKOUT'
    CONSOLIDATION = 'CONSOLIDATION'
    REVERSAL = 'REVERSAL'


@dataclass(slots=True)
class SpikeEvent:
    symbol: str
    price: float
    timestamp: float
    polarity: int
    delta_pct: float


class NeuromorphicMarketEncoder:
    def __init__(self, event_bus: EventBus, threshold_pct: float = 0.0015, refractory_period: float = 0.5) -> None:
        self.event_bus = event_bus
        self.threshold_pct = threshold_pct
        self.refractory_period = refractory_period
        self.last_spike_ts: dict[str, float] = defaultdict(float)
        self.last_price: dict[str, float] = {}
        self.spike_history: dict[str, deque[SpikeEvent]] = defaultdict(lambda: deque(maxlen=200))
        self.detected_patterns: dict[str, PatternType] = {}
        self._running = False

    async def encode_stream(self, symbol: str, price_feed: AsyncIterator[float]) -> AsyncIterator[SpikeEvent]:
        async for price in price_feed:
            spike = self._encode_price(symbol, float(price), time.time())
            if spike is not None:
                yield spike

    def _encode_price(self, symbol: str, price: float, timestamp: float) -> SpikeEvent | None:
        previous = self.last_price.get(symbol)
        self.last_price[symbol] = price
        if previous is None:
            return None
        delta_pct = (price - previous) / previous
        if abs(delta_pct) < self.threshold_pct:
            return None
        if timestamp - self.last_spike_ts[symbol] < self.refractory_period:
            return None
        self.last_spike_ts[symbol] = timestamp
        spike = SpikeEvent(symbol=symbol, price=price, timestamp=timestamp, polarity=1 if delta_pct > 0 else -1, delta_pct=delta_pct)
        self.spike_history[symbol].append(spike)
        return spike

    def detect_pattern(self, spike_history: list[SpikeEvent], window: int = 50) -> PatternType:
        history = spike_history[-window:]
        if len(history) < 3:
            return PatternType.CONSOLIDATION
        polarities = [spike.polarity for spike in history]
        ratio = sum(1 for polarity in polarities if polarity > 0) / len(polarities)
        intervals = [history[i].timestamp - history[i - 1].timestamp for i in range(1, len(history))]
        mean_interval = sum(intervals) / len(intervals)
        bursty = sum(1 for value in intervals if value < self.refractory_period * 1.5) / len(intervals)
        if bursty > 0.6 and ratio > 0.7:
            return PatternType.BREAKOUT
        if bursty > 0.6 and ratio < 0.3:
            return PatternType.REVERSAL
        if ratio > 0.65:
            return PatternType.ACCUMULATION
        if ratio < 0.35:
            return PatternType.DISTRIBUTION
        if mean_interval > 2.5:
            return PatternType.CONSOLIDATION
        return PatternType.REVERSAL

    async def on_candle(self, payload: dict[str, Any]) -> None:
        symbol = str(payload['symbol'])
        spike = self._encode_price(symbol, float(payload['close']), time.time())
        if spike is None:
            return
        await self.event_bus.publish(f'neuromorphic.spike.{symbol}', {'symbol': spike.symbol, 'price': spike.price, 'timestamp': spike.timestamp, 'polarity': spike.polarity, 'delta_pct': spike.delta_pct})
        pattern = self.detect_pattern(list(self.spike_history[symbol]))
        self.detected_patterns[symbol] = pattern
        await self.event_bus.publish(f'neuromorphic.pattern.{symbol}', {'symbol': symbol, 'pattern': pattern.value, 'timestamp': spike.timestamp})

    async def start(self) -> None:
        if not self._running:
            self.event_bus.subscribe_pattern('nexus.candle.*', self.on_candle)
            self._running = True

    async def run(self) -> None:
        await self.start()
        while self._running:
            await asyncio.sleep(0.5)

    def health(self) -> dict[str, Any]:
        spike_rates = {symbol: len(history) for symbol, history in self.spike_history.items()}
        return {'status': 'ok', 'response_time_ms': 0.0, 'spike_rates': spike_rates, 'detected_patterns': {symbol: pattern.value for symbol, pattern in self.detected_patterns.items()}}
