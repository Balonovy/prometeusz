from __future__ import annotations

import time
from typing import Any

from neural_os.state_manager import StateManager


class AutonomousRiskManager:
    def __init__(self, state_manager: StateManager, correlation_graph: Any | None = None) -> None:
        self.state_manager = state_manager
        self.correlation_graph = correlation_graph
        self.override_regime: str | None = None
        self.history: list[dict[str, Any]] = []
        self.loss_streak = 0
        self.current_state = {'total_exposure': 0.0, 'drawdown_current': 0.0, 'var_95_1h': 0.0, 'correlation_risk': 0.0, 'regime': 'ranging'}

    def detect_regime(self, prices: dict[str, list[float]]) -> str:
        flattened = [value for series in prices.values() for value in series[-20:]]
        if not flattened:
            return 'ranging'
        volatility = (max(flattened) - min(flattened)) / max(sum(flattened) / len(flattened), 1e-9)
        slope = flattened[-1] - flattened[0]
        if volatility > 0.2:
            return 'crisis'
        if slope > 0:
            return 'bull'
        if slope < 0:
            return 'bear'
        return 'ranging'

    async def assess(self, proposed_decisions: list[dict[str, Any]], portfolio: dict[str, Any], market_state: dict[str, Any]) -> dict[str, Any]:
        exposure = sum(abs(weight) for weight in portfolio.get('weights', [])) if portfolio else 0.0
        drawdown = float(market_state.get('drawdown_current', 0.0))
        var_95 = float(market_state.get('var_95_1h', 0.0))
        correlation_risk = float((market_state.get('cascade_alert') or {}).get('quantum_coherence', 0.0))
        regime = self.override_regime or self.detect_regime(market_state.get('prices', {}))
        hard_reasons = []
        if exposure > 0.8:
            hard_reasons.append('exposure_limit')
        if drawdown > 0.15:
            hard_reasons.append('drawdown_limit')
        if var_95 > 0.05:
            hard_reasons.append('var_limit')
        cascade = market_state.get('cascade_alert') or {}
        if cascade.get('triggered'):
            hard_reasons.append('cascade_block')
        position_scale = 1.0
        if correlation_risk > 0.7:
            position_scale *= 0.5
        if regime == 'crisis':
            position_scale = 0.0
        if self.loss_streak >= 3:
            position_scale = 0.0
        assessment = {'hard_blocked': bool(hard_reasons), 'hard_reasons': hard_reasons, 'position_scale': position_scale, 'allowed_actions': ['HOLD'] if position_scale == 0.0 else ['BUY', 'SELL', 'HOLD'], 'risk_state': {'total_exposure': exposure, 'drawdown_current': drawdown, 'var_95_1h': var_95, 'correlation_risk': correlation_risk, 'regime': regime}, 'timestamp': time.time()}
        self.current_state = assessment['risk_state']
        self.history.append(assessment)
        self.history = self.history[-100:]
        await self.state_manager.set('nexus:risk:last', assessment, ttl=3600)
        return assessment

    def set_override(self, regime: str) -> None:
        self.override_regime = regime

    def health(self) -> dict[str, Any]:
        return {'status': 'ok', 'response_time_ms': 0.0, 'regime': self.current_state['regime'], 'history': len(self.history)}
