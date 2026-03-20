from __future__ import annotations

import math
from typing import Any

try:
    import pennylane as qml
    import numpy as np
except ImportError:  # pragma: no cover
    qml = None
    np = None


class QuantumSimulator:
    def __init__(self, wires: int = 4) -> None:
        self.wires = wires
        self.available = qml is not None and np is not None
        self.device = qml.device('default.qubit', wires=wires) if self.available else None
        self.last_result: dict[str, Any] | None = None

    def run_vqe(self, steps: int = 24) -> dict[str, Any]:
        if not self.available:
            params = [0.1, 0.2, 0.3, 0.4]
            energy = sum(math.cos(value) for value in params[:2]) / -2
            result = {'backend': 'fallback', 'energy': energy, 'params': params, 'parameters': params, 'circuit_depth': 7, 'n_qubits': self.wires, 'steps': steps}
            self.last_result = result
            return result

        @qml.qnode(self.device)
        def vqe_circuit(params: Any) -> Any:
            for i in range(self.wires):
                qml.RY(params[i], wires=i)
            for i in range(self.wires - 1):
                qml.CNOT(wires=[i, i + 1])
            return qml.expval(qml.PauliZ(0) @ qml.PauliZ(1))

        params = np.array([0.11, 0.22, 0.33, 0.44], requires_grad=True)
        optimizer = qml.AdamOptimizer(stepsize=0.12)
        for _ in range(steps):
            params = optimizer.step(vqe_circuit, params)
        energy = float(vqe_circuit(params))
        result = {'backend': 'default.qubit', 'energy': energy, 'params': [float(v) for v in params], 'parameters': [float(v) for v in params], 'circuit_depth': 7, 'n_qubits': self.wires, 'steps': steps}
        self.last_result = result
        return result
