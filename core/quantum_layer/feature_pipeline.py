from __future__ import annotations

import math
from typing import Any

from core.ai_module.temporal_memory import TemporalPatternMemory


class QuantumFeaturePipeline:
    def __init__(self, temporal_memory: TemporalPatternMemory, market_encoder: Any | None = None) -> None:
        self.temporal_memory = temporal_memory
        self.market_encoder = market_encoder
        self.cache: dict[str, list[float]] = {}

    def _classical_features(self, closes: list[float]) -> list[float]:
        if len(closes) < 3:
            return [0.0] * 20
        returns = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes)) if closes[i - 1] > 0]
        mean = sum(returns) / len(returns)
        variance = sum((value - mean) ** 2 for value in returns) / len(returns)
        volatility = math.sqrt(variance)
        skew = sum((value - mean) ** 3 for value in returns) / len(returns) if volatility else 0.0
        kurt = sum((value - mean) ** 4 for value in returns) / len(returns) if volatility else 0.0
        autocorr = []
        for lag in range(1, 6):
            if len(returns) <= lag:
                autocorr.append(0.0)
                continue
            left = returns[:-lag]
            right = returns[lag:]
            mean_l = sum(left) / len(left)
            mean_r = sum(right) / len(right)
            num = sum((a - mean_l) * (b - mean_r) for a, b in zip(left, right))
            den = math.sqrt(sum((a - mean_l) ** 2 for a in left) * sum((b - mean_r) ** 2 for b in right))
            autocorr.append(num / den if den else 0.0)
        entropy = -sum(abs(value) * math.log(abs(value) + 1e-9) for value in returns[-10:]) / max(len(returns[-10:]), 1)
        features = [mean, volatility, skew, kurt, entropy]
        features.extend(autocorr)
        while len(features) < 20:
            features.append(0.0)
        return features[:20]

    def _quantum_kernel_features(self, vector: list[float]) -> list[float]:
        window = vector[:4]
        kernel = sum(value * value for value in window) / max(len(window), 1)
        return [kernel, math.sqrt(abs(kernel))]

    def _spike_features(self, symbol: str) -> list[float]:
        if self.market_encoder is None:
            return [0.0] * 6
        history = list(self.market_encoder.spike_history.get(symbol, []))
        if not history:
            return [0.0] * 6
        recent = history[-10:]
        mean_interval = sum(recent[i].timestamp - recent[i - 1].timestamp for i in range(1, len(recent))) / max(len(recent) - 1, 1)
        polarity_ratio = sum(1 for spike in recent if spike.polarity > 0) / len(recent)
        return [len(recent), len(history[-50:]), sum(1 for spike in recent if abs(spike.delta_pct) > 0.003), 0.0, polarity_ratio, mean_interval]

    def _temporal_features(self, symbol: str, sequence: list[list[float]]) -> list[float]:
        analogues = self.temporal_memory.find_analogues(sequence, symbol, top_k=5, similarity_threshold=0.0)
        forecast = self.temporal_memory.synthesize_forecast(analogues)
        best_similarity = analogues[0].similarity if analogues else 0.0
        return [best_similarity, forecast['1h_forecast'], forecast['4h_forecast'], float(forecast['n_analogues']), forecast['confidence_interval_95']]

    def transform(self, symbol: str, candles: list[dict[str, Any]]) -> list[float]:
        closes = [float(candle['close']) for candle in candles[-50:] if candle.get('close') is not None]
        classical = self._classical_features(closes)
        quantum = self._quantum_kernel_features(classical)
        sequence = [[float(candle.get(key, 0.0)) for key in ('open', 'high', 'low', 'close', 'volume', 'spread', 'funding_rate')] + [float(index)] for index, candle in enumerate(candles[-50:])]
        temporal = self._temporal_features(symbol, sequence)
        spike = self._spike_features(symbol)
        feature_vector = classical + quantum + spike + temporal
        while len(feature_vector) < 64:
            feature_vector.append(0.0)
        self.cache[symbol] = feature_vector[:64]
        return self.cache[symbol]

    async def warm_up(self, market_data: Any | None = None) -> None:
        if market_data is None:
            return
        for symbol, candles in market_data.candle_snapshot().items():
            self.transform(symbol, candles)

    def health(self) -> dict[str, Any]:
        return {'status': 'ok', 'response_time_ms': 0.0, 'cached_symbols': len(self.cache)}

    def labeled_features(self, symbol: str) -> dict[str, Any]:
        vector = self.cache.get(symbol, [0.0] * 64)
        return {'symbol': symbol, 'features': vector, 'shape': len(vector)}
