from __future__ import annotations

import math
from typing import Any

from nexus.quantum_signals import QuantumSignalClassifier


class SignalEngine:
    def __init__(self) -> None:
        self._signals: dict[str, dict[str, Any]] = {}
        self.quantum_classifier = QuantumSignalClassifier()

    def compute_signal(self, symbol: str, candles: list[dict[str, Any]]) -> dict[str, Any]:
        closes = [float(candle['close']) for candle in candles if candle.get('close') is not None]
        if not closes:
            signal = {'symbol': symbol, 'action': 'HOLD', 'confidence': 0.0, 'trend': 'neutral', 'indicators': {}, 'quantum_score': 0.0}
            self._signals[symbol] = signal
            return signal
        ema_values = {period: self._ema(closes, period) for period in (8, 13, 21, 50, 200)}
        rsi = self._rsi(closes, 14)
        bb = self._bollinger(closes, 20)
        sar = self._parabolic_sar(closes)
        quantum_score = self.quantum_classifier.score_window(closes[-5:])
        action = 'HOLD'
        trend = 'neutral'
        confidence = 0.5
        if ema_values[8] > ema_values[21] > ema_values[50] and rsi < 70:
            action = 'BUY'
            trend = 'bullish'
            confidence = min(0.99, 0.55 + quantum_score * 0.3 + max(0.0, (ema_values[8] - ema_values[21]) / max(closes[-1], 1e-9)))
        elif ema_values[8] < ema_values[21] < ema_values[50] and rsi > 30:
            action = 'SELL'
            trend = 'bearish'
            confidence = min(0.99, 0.55 + quantum_score * 0.3 + max(0.0, (ema_values[21] - ema_values[8]) / max(closes[-1], 1e-9)))
        signal = {'symbol': symbol, 'action': action, 'trend': trend, 'confidence': round(float(confidence), 4), 'price': float(closes[-1]), 'quantum_score': round(float(quantum_score), 4), 'indicators': {'ema': {str(k): round(float(v), 6) for k, v in ema_values.items()}, 'rsi_14': round(float(rsi), 4), 'bollinger': bb, 'sar': round(float(sar), 6)}}
        self._signals[symbol] = signal
        return signal

    def generate_signal(self, symbol: str, candles: list[dict[str, Any]]) -> dict[str, Any]:
        return self.compute_signal(symbol, candles)

    def compute_all(self, market_data: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
        return {symbol: self.compute_signal(symbol, candles) for symbol, candles in market_data.items()}

    def latest_signals(self) -> dict[str, dict[str, Any]]:
        return dict(self._signals)

    def _ema(self, closes: list[float], period: int) -> float:
        ema = closes[0]
        alpha = 2 / (period + 1)
        for value in closes[1:]:
            ema = alpha * value + (1 - alpha) * ema
        return ema

    def _rsi(self, closes: list[float], period: int) -> float:
        if len(closes) < 2:
            return 50.0
        deltas = [closes[index] - closes[index - 1] for index in range(1, len(closes))]
        gains = [max(delta, 0.0) for delta in deltas][-period:]
        losses = [abs(min(delta, 0.0)) for delta in deltas][-period:]
        avg_gain = sum(gains) / len(gains) if gains else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0
        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def _bollinger(self, closes: list[float], period: int) -> dict[str, float]:
        window = closes[-period:] if len(closes) >= period else closes
        mean = sum(window) / len(window)
        variance = sum((value - mean) ** 2 for value in window) / len(window)
        std = math.sqrt(variance)
        upper = mean + 2 * std
        lower = mean - 2 * std
        bandwidth = (upper - lower) / mean if mean else 0.0
        return {'upper': round(upper, 6), 'middle': round(mean, 6), 'lower': round(lower, 6), 'bandwidth': round(float(bandwidth), 6)}

    def _parabolic_sar(self, closes: list[float], step: float = 0.02, max_step: float = 0.2) -> float:
        sar = closes[0]
        extreme = closes[0]
        accel = step
        uptrend = True
        for price in closes[1:]:
            sar = sar + accel * (extreme - sar)
            if uptrend:
                if price > extreme:
                    extreme = price
                    accel = min(accel + step, max_step)
                elif price < sar:
                    uptrend = False
                    sar = extreme
                    extreme = price
                    accel = step
            else:
                if price < extreme:
                    extreme = price
                    accel = min(accel + step, max_step)
                elif price > sar:
                    uptrend = True
                    sar = extreme
                    extreme = price
                    accel = step
        return sar

    def health(self) -> dict[str, Any]:
        return {'status': 'ok', 'response_time_ms': 0.0, 'symbols': len(self._signals)}
