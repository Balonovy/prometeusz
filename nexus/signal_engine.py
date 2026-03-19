from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class SignalResult:
    symbol: str
    regime: str
    confidence: float
    ema_fast: float
    ema_slow: float


class SignalEngine:
    def _ema(self, prices: list[float], span: int) -> float:
        multiplier = 2 / (span + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = (price - ema) * multiplier + ema
        return ema

    def generate(self, symbol: str, prices: list[float]) -> dict[str, float | str]:
        ema8 = self._ema(prices, 8)
        ema21 = self._ema(prices, 21)
        regime = 'bullish' if ema8 >= ema21 else 'bearish'
        confidence = min(abs(ema8 - ema21) / max(abs(ema21), 1.0) * 100, 99.0)
        return asdict(SignalResult(symbol=symbol, regime=regime, confidence=round(confidence, 4), ema_fast=ema8, ema_slow=ema21))
