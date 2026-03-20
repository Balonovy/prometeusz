from __future__ import annotations

import math
from typing import Iterable

try:
    import pennylane as qml
except ImportError:  # pragma: no cover
    qml = None


class QuantumSignalClassifier:
    def __init__(self) -> None:
        self.available = qml is not None
        self.device = qml.device('default.qubit', wires=5) if self.available else None

    def score_window(self, window: Iterable[float]) -> float:
        values = [float(value) for value in window]
        if not values:
            return 0.0
        while len(values) < 5:
            values.insert(0, values[0])
        values = values[-5:]
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        scale = math.sqrt(variance) or 1.0
        normalized = [(value - mean) / scale for value in values]
        if not self.available:
            slope = normalized[-1] - normalized[0]
            score = 0.5 + 0.2 * math.tanh(slope)
            return max(0.0, min(1.0, score))

        @qml.qnode(self.device)
        def circuit(features):
            qml.AngleEmbedding(features, wires=range(5), rotation='Y')
            for index in range(4):
                qml.CNOT(wires=[index, index + 1])
            return qml.expval(qml.PauliZ(0))

        raw = float(circuit(normalized))
        return max(0.0, min(1.0, (1 - raw) / 2))
