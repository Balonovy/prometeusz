from __future__ import annotations

import asyncio
import math
import time
from typing import Any

from neural_os.event_bus import EventBus


class QuantumCorrelationGraph:
    def __init__(self, event_bus: EventBus, threshold: float = 0.65) -> None:
        self.event_bus = event_bus
        self.threshold = threshold
        self.last_matrix: list[list[float]] = []
        self.last_graph_state: list[float] = []
        self.last_cascade: dict[str, Any] | None = None
        self._running = False

    def _pearson(self, xs: list[float], ys: list[float]) -> float:
        if len(xs) != len(ys) or len(xs) < 2:
            return 0.0
        mean_x = sum(xs) / len(xs)
        mean_y = sum(ys) / len(ys)
        num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
        den_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
        den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
        return num / (den_x * den_y) if den_x and den_y else 0.0

    def build_correlation_matrix(self, candles: dict[str, list[dict[str, Any]]]) -> list[list[float]]:
        symbols = sorted(candles)
        matrix: list[list[float]] = []
        series = {symbol: [float(row['close']) for row in candles[symbol][-200:]] for symbol in symbols}
        for left in symbols:
            row = []
            for right in symbols:
                row.append(round(self._pearson(series[left][-50:], series[right][-50:]), 4))
            matrix.append(row)
        self.last_matrix = matrix
        return matrix

    def encode_as_graph_state(self, corr_matrix: list[list[float]]) -> list[float]:
        activation = []
        limit = min(8, len(corr_matrix))
        for index in range(limit):
            strength = sum(abs(value) for value in corr_matrix[index][:limit] if abs(value) > self.threshold)
            activation.append(round(min(1.0, strength / max(limit, 1)), 4))
        self.last_graph_state = activation
        return activation

    def detect_cascade(self, activation_vector: list[float], symbols: list[str] | None = None) -> dict[str, Any]:
        symbols = symbols or []
        active_indexes = [index for index, value in enumerate(activation_vector) if value > 0.45]
        affected = [symbols[index] for index in active_indexes if index < len(symbols)]
        triggered = len(active_indexes) > 3
        cascade_type = 'breakout' if triggered else 'rotation' if len(active_indexes) >= 2 else 'contagion' if any(value < -0.6 for row in self.last_matrix for value in row) else 'rotation'
        recommended = 'VETO' if cascade_type == 'contagion' else 'BUY' if triggered else 'OBSERVE'
        alert = {'triggered': triggered, 'affected_pairs': affected, 'cascade_type': cascade_type, 'quantum_coherence': round(sum(activation_vector) / max(len(activation_vector), 1), 4), 'recommended_action': recommended}
        self.last_cascade = alert
        return alert

    async def monitor_correlations(self, market_data: Any, interval: float = 60.0) -> None:
        self._running = True
        while self._running:
            candles = market_data.candle_snapshot()
            symbols = sorted(candles)
            matrix = self.build_correlation_matrix(candles)
            activation = self.encode_as_graph_state(matrix)
            alert = self.detect_cascade(activation, symbols)
            await self.event_bus.publish('quantum.correlation.update', {'matrix': matrix, 'graph_state': activation, 'cascade': alert, 'timestamp': time.time()})
            await asyncio.sleep(interval)

    def health(self) -> dict[str, Any]:
        return {'status': 'ok', 'response_time_ms': 0.0, 'matrix_size': len(self.last_matrix), 'cascade': self.last_cascade}
