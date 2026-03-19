from __future__ import annotations

import math
from dataclasses import dataclass

try:
    import pennylane as qml
    from pennylane import numpy as np
except Exception:  # pragma: no cover
    qml = None
    np = None

from config.quantum_config import DEFAULT_QUANTUM_CONFIG


@dataclass(slots=True)
class VariationalResult:
    energy: float
    parameters: list[float]
    expectation_z: list[float]


class QuantumSimulator:
    def __init__(self) -> None:
        self.config = DEFAULT_QUANTUM_CONFIG
        self._circuit = None
        if qml is not None and np is not None:
            self.device = qml.device(self.config.device_name, wires=self.config.wires, shots=self.config.shots)

            @qml.qnode(self.device)
            def circuit(weights: np.ndarray) -> tuple[float, ...]:
                reshaped = weights.reshape(self.config.layers, self.config.wires)
                for layer in range(self.config.layers):
                    for wire in range(self.config.wires):
                        qml.RY(reshaped[layer][wire], wires=wire)
                    for wire in range(self.config.wires - 1):
                        qml.CNOT(wires=[wire, wire + 1])
                return tuple(qml.expval(qml.PauliZ(wire)) for wire in range(self.config.wires))

            self._circuit = circuit

    def run_vqe(self, steps: int = 25, step_size: float = 0.15) -> VariationalResult:
        if self._circuit is not None and np is not None and qml is not None:
            weights = np.array(np.linspace(0.1, 0.8, self.config.layers * self.config.wires), requires_grad=True)
            optimizer = qml.GradientDescentOptimizer(step_size=step_size)

            def cost_fn(current_weights):
                expectations = np.array(self._circuit(current_weights))
                return float(np.mean(expectations))

            for _ in range(steps):
                weights = optimizer.step(cost_fn, weights)
            expectation = [float(value) for value in self._circuit(weights)]
            energy = float(sum(expectation) / len(expectation))
            return VariationalResult(energy=energy, parameters=[float(x) for x in weights], expectation_z=expectation)

        parameters = [0.1 + index * 0.1 for index in range(self.config.layers * self.config.wires)]
        for _ in range(steps):
            parameters = [value - step_size * math.sin(value) * 0.1 for value in parameters]
        expectation = [math.cos(parameters[index]) for index in range(self.config.wires)]
        energy = sum(expectation) / len(expectation)
        return VariationalResult(energy=float(energy), parameters=[float(x) for x in parameters], expectation_z=[float(x) for x in expectation])
