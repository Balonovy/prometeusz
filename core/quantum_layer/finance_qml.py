from __future__ import annotations

from core.quantum_layer.optimizer import PortfolioOptimizationResult, QuantumOptimizer


class QuantumFinanceModel:
    def __init__(self, optimizer: QuantumOptimizer | None = None) -> None:
        self.optimizer = optimizer or QuantumOptimizer()

    def optimize_demo_portfolio(self) -> PortfolioOptimizationResult:
        returns = [0.11, 0.07, 0.13, 0.05]
        risk = [0.03, 0.02, 0.08, 0.01]
        return self.optimizer.optimize_portfolio(returns=returns, risk=risk, budget=2)
