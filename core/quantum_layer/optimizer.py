from __future__ import annotations

from dataclasses import dataclass

from core.quantum_layer.simulator import QuantumSimulator


@dataclass(slots=True)
class PortfolioOptimizationResult:
    selection: list[int]
    score: float
    vqe_energy: float


class QuantumOptimizer:
    def __init__(self, simulator: QuantumSimulator | None = None) -> None:
        self.simulator = simulator or QuantumSimulator()

    def optimize_portfolio(self, returns: list[float], risk: list[float], budget: int = 2) -> PortfolioOptimizationResult:
        best_score = float('-inf')
        best_selection = [0] * len(returns)
        for mask in range(1, 2 ** len(returns)):
            bits = [(mask >> idx) & 1 for idx in range(len(returns))]
            if sum(bits) > budget:
                continue
            reward = sum(r * b for r, b in zip(returns, bits))
            penalty = sum(rv * b for rv, b in zip(risk, bits))
            score = reward - penalty
            if score > best_score:
                best_score = score
                best_selection = bits
        vqe = self.simulator.run_vqe(steps=10)
        return PortfolioOptimizationResult(selection=best_selection, score=round(best_score, 6), vqe_energy=vqe.energy)
