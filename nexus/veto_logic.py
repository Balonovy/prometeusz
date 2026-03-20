from __future__ import annotations

from typing import Any


class VetoSystem:
    def __init__(self, min_confidence: float = 0.6) -> None:
        self.min_confidence = min_confidence
        self._active_vetos: list[dict[str, Any]] = []

    def evaluate(self, signal: dict[str, Any], market_snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
        market_snapshot = market_snapshot or {}
        reasons: list[str] = []
        indicators = signal.get('indicators', {})
        rsi = float(indicators.get('rsi_14', 50.0))
        bandwidth = float(indicators.get('bollinger', {}).get('bandwidth', 0.0))
        spread = float(market_snapshot.get('spread', 0.0) or 0.0)
        funding_rate = float(market_snapshot.get('funding_rate', 0.0) or 0.0)
        confidence = float(signal.get('confidence', 0.0))
        if confidence < self.min_confidence:
            reasons.append('confidence_below_threshold')
        if rsi >= 78 or rsi <= 22:
            reasons.append('rsi_extreme')
        if abs(funding_rate) > 0.02:
            reasons.append('funding_rate_extreme')
        if spread > 0.005:
            reasons.append('spread_too_wide')
        if bandwidth < 0.002:
            reasons.append('low_bb_bandwidth')
        status = 'VETO' if reasons else 'CLEAR'
        result = {'status': status, 'pair': signal.get('symbol'), 'reasons': reasons, 'severity': 'high' if len(reasons) >= 2 else 'medium' if reasons else 'low', 'signal': signal}
        if reasons:
            self._active_vetos.append(result)
            self._active_vetos = self._active_vetos[-100:]
        return result

    def evaluate_all(self, signals: dict[str, dict[str, Any]], market_snapshots: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        return {symbol: self.evaluate(signal, market_snapshots.get(symbol, {})) for symbol, signal in signals.items()}

    def active_vetos(self) -> list[dict[str, Any]]:
        return list(self._active_vetos[-50:])

    def health(self) -> dict[str, Any]:
        return {'status': 'ok', 'response_time_ms': 0.0, 'active_vetos': len(self._active_vetos)}
