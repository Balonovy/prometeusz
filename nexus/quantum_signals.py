from __future__ import annotations

import math


class QuantumSignalEnhancer:
    def score_pattern(self, prices: list[float]) -> float:
        if len(prices) < 2:
            return 0.0
        diffs = [prices[index] - prices[index - 1] for index in range(1, len(prices))]
        norm = sum(abs(diff) for diff in diffs) or 1.0
        projection = sum(math.sin(diff / norm) for diff in diffs)
        return round((projection / len(diffs) + 1) / 2, 4)
