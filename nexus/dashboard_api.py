from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from nexus.market_data import BybitMarketDataClient
from nexus.quantum_signals import QuantumSignalEnhancer
from nexus.signal_engine import SignalEngine
from nexus.veto_logic import VetoLogic


class DashboardService:
    def __init__(self, market_data: BybitMarketDataClient | None = None) -> None:
        self.market_data = market_data or BybitMarketDataClient()
        self.signal_engine = SignalEngine()
        self.quantum = QuantumSignalEnhancer()
        self.veto = VetoLogic()

    def build_signals(self, snapshots: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for snapshot in snapshots:
            price = float(snapshot['price'])
            synthetic_prices = [price * (1 + offset / 1000) for offset in range(-10, 11)]
            signal = self.signal_engine.generate(snapshot['symbol'], synthetic_prices)
            signal['quantum_score'] = self.quantum.score_pattern(synthetic_prices)
            signal['veto'] = self.veto.evaluate(signal, float(snapshot['funding_rate']))
            results.append(signal)
        return results
