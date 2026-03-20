from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any

try:
    import pennylane as qml
    import numpy as np
except ImportError:  # pragma: no cover
    qml = None
    np = None


@dataclass(slots=True)
class PortfolioAllocation:
    pairs: list[str]
    weights: list[float]
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    quantum_confidence: float


class QuantumPortfolioEngine:
    def __init__(self, risk_aversion: float = 0.5, layers: int = 4, qubits: int = 8, iterations: int = 200) -> None:
        self.risk_aversion = risk_aversion
        self.layers = layers
        self.qubits = qubits
        self.iterations = iterations
        self.last_allocation: PortfolioAllocation | None = None
        self.last_risk_report: dict[str, float] | None = None

    async def optimize_live(self, market_data: dict[str, list[dict[str, Any]]]) -> PortfolioAllocation:
        stats = []
        for pair, candles in sorted(market_data.items()):
            closes = [float(row['close']) for row in candles[-200:] if row.get('close') is not None]
            if len(closes) < 3:
                continue
            returns = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes))]
            mean_return = sum(returns) / len(returns)
            variance = sum((value - mean_return) ** 2 for value in returns) / len(returns)
            stats.append((pair, mean_return, variance))
        if not stats:
            allocation = PortfolioAllocation([], [], 0.0, 0.0, 0.0, 0.0)
            self.last_allocation = allocation
            return allocation
        raw_scores = self._run_qaoa(stats)
        ranked = sorted(zip(stats, raw_scores), key=lambda item: item[1], reverse=True)[:5]
        score_sum = sum(max(score, 1e-9) for _, score in ranked)
        weights = [max(score, 1e-9) / score_sum for _, score in ranked]
        expected_return = sum(weight * stat[1] for (stat, _), weight in zip(ranked, weights)) * 252
        expected_volatility = math.sqrt(sum((weight ** 2) * stat[2] for (stat, _), weight in zip(ranked, weights))) * math.sqrt(252)
        sharpe_ratio = expected_return / expected_volatility if expected_volatility else 0.0
        allocation = PortfolioAllocation([stat[0] for stat, _ in ranked], [float(weight) for weight in weights], float(expected_return), float(expected_volatility), float(sharpe_ratio), float(sum(score for _, score in ranked) / len(ranked)))
        self.last_allocation = allocation
        self.last_risk_report = self.monte_carlo_risk(allocation)
        return allocation

    def _run_qaoa(self, stats: list[tuple[str, float, float]]) -> list[float]:
        if qml is None or np is None:
            scores = []
            for _, mean_return, variance in stats:
                raw = mean_return - self.risk_aversion * variance
                scores.append(max(0.0, raw + 0.5))
            peak = max(scores) or 1.0
            return [score / peak for score in scores]
        wires = min(self.qubits, len(stats))
        dev = qml.device('default.qubit', wires=wires)
        qubo = [self.risk_aversion * variance - mean_return for _, mean_return, variance in stats[:wires]]

        @qml.qnode(dev)
        def circuit(gammas, betas):
            for wire in range(wires):
                qml.Hadamard(wires=wire)
            for layer in range(self.layers):
                for wire in range(wires):
                    qml.RZ(gammas[layer] * qubo[wire], wires=wire)
                    qml.RX(betas[layer], wires=wire)
                for wire in range(wires - 1):
                    qml.CNOT(wires=[wire, wire + 1])
            return [qml.expval(qml.PauliZ(wire)) for wire in range(wires)]

        gammas = np.array([0.2] * self.layers, requires_grad=True)
        betas = np.array([0.3] * self.layers, requires_grad=True)
        optimizer = qml.AdamOptimizer(stepsize=0.05)

        def objective(params):
            g, b = params
            expectation = circuit(g, b)
            return -sum((1 - value) / 2 for value in expectation) / wires

        params = (gammas, betas)
        for _ in range(self.iterations):
            params = optimizer.step(objective, params)
        expectation = circuit(*params)
        scores = [max(0.0, (1 - float(value)) / 2) for value in expectation]
        peak = max(scores) or 1.0
        normalized = [score / peak for score in scores]
        if len(stats) > wires:
            normalized.extend([0.5 for _ in range(len(stats) - wires)])
        return normalized

    def monte_carlo_risk(self, allocation: PortfolioAllocation, n_simulations: int = 10000) -> dict[str, float]:
        if not allocation.weights:
            return {'VaR_95': 0.0, 'CVaR_95': 0.0, 'max_drawdown': 0.0, 'sharpe_ratio': 0.0}
        rng = random.Random(42)
        daily_mean = allocation.expected_return / 252
        daily_vol = allocation.expected_volatility / math.sqrt(252) if allocation.expected_volatility else 0.01
        final_returns = []
        max_drawdowns = []
        for _ in range(n_simulations):
            capital = 1.0
            peak = 1.0
            worst_drawdown = 0.0
            for _day in range(252):
                daily_return = rng.gauss(daily_mean, daily_vol)
                capital *= (1 + daily_return)
                peak = max(peak, capital)
                worst_drawdown = max(worst_drawdown, 1 - capital / peak)
            final_returns.append(capital - 1)
            max_drawdowns.append(worst_drawdown)
        final_returns.sort()
        idx = max(0, int(0.05 * len(final_returns)) - 1)
        var_95 = final_returns[idx]
        tail = [value for value in final_returns if value <= var_95] or [var_95]
        cvar_95 = sum(tail) / len(tail)
        mean_return = sum(final_returns) / len(final_returns)
        variance = sum((value - mean_return) ** 2 for value in final_returns) / len(final_returns)
        sharpe = mean_return / (math.sqrt(variance) + 1e-9)
        report = {'VaR_95': float(var_95), 'CVaR_95': float(cvar_95), 'max_drawdown': float(max(max_drawdowns)), 'sharpe_ratio': float(sharpe)}
        self.last_risk_report = report
        return report

    def health(self) -> dict[str, Any]:
        return {'status': 'ok', 'response_time_ms': 0.0, 'iterations': self.iterations, 'has_allocation': self.last_allocation is not None}
