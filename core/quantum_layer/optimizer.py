from __future__ import annotations

from typing import Any

from core.quantum_layer.simulator import QuantumSimulator


class QuantumOptimizer:
    def __init__(self) -> None:
        self.simulator = QuantumSimulator()
        self.iterations = 24
        self.last_result: dict[str, Any] | None = None

    def optimize(self) -> dict[str, Any]:
        result = self.simulator.run_vqe(steps=self.iterations)
        result['algorithm'] = 'vqe'
        self.last_result = result
        return result

    def current_market_graph_state(self) -> dict[str, Any]:
        result = self.last_result or self.optimize()
        return {'status': 'ok', 'energy': result['energy'], 'backend': result['backend'], 'n_qubits': result['n_qubits']}

    def tune_iterations(self, factor: float) -> None:
        self.iterations = max(4, int(self.iterations * factor))

    def health(self) -> dict[str, Any]:
        return {'status': 'ok', 'response_time_ms': 0.0, 'iterations': self.iterations, 'last_energy': (self.last_result or {}).get('energy')}
