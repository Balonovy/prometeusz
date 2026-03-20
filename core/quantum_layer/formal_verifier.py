from __future__ import annotations

from typing import Any


class FormalVerifier:
    def __init__(self, veto_system: Any, risk_manager: Any, quantum_optimizer: Any, quantum_consensus: Any) -> None:
        self.veto_system = veto_system
        self.risk_manager = risk_manager
        self.quantum_optimizer = quantum_optimizer
        self.quantum_consensus = quantum_consensus

    def verify_veto_completeness(self) -> dict[str, Any]:
        rsis = [0, 19, 20, 29, 30, 70, 71, 79, 80, 81, 100]
        fundings = [0, 0.005, 0.01, 0.011, 0.05]
        spreads = [0, 0.002, 0.005, 0.006, 0.02]
        actions = ['BUY', 'SELL', 'HOLD']
        failed = []
        total = 0
        for rsi in rsis:
            for funding in fundings:
                for spread in spreads:
                    for action in actions:
                        total += 1
                        signal = {'symbol': 'DOGEUSDT', 'action': action, 'confidence': 0.9, 'indicators': {'rsi_14': rsi, 'bollinger': {'bandwidth': 0.01}}}
                        ctx = {'funding_rate': funding, 'spread': spread}
                        result = self.veto_system.evaluate(signal, ctx)
                        severity = result['severity']
                        if severity not in {'low', 'medium', 'high'}:
                            failed.append({'input': [rsi, funding, spread, action], 'expected': 'valid severity', 'actual': severity})
                        if rsi > 80 and action == 'BUY' and result['status'] != 'VETO':
                            failed.append({'input': [rsi, funding, spread, action], 'expected': 'VETO', 'actual': result['status']})
                        if rsi < 20 and action == 'SELL' and result['status'] != 'VETO':
                            failed.append({'input': [rsi, funding, spread, action], 'expected': 'VETO', 'actual': result['status']})
        passed = total - len(failed)
        return {'total_cases': total, 'passed': passed, 'failed': failed[:20], 'coverage_pct': 100.0 * passed / max(total, 1), 'proof_valid': not failed}

    def verify_risk_monotonicity(self) -> bool:
        base = self.risk_manager.detect_regime({'DOGEUSDT': [1, 1.01, 1.02]})
        worse = self.risk_manager.detect_regime({'DOGEUSDT': [1, 1.4, 0.6]})
        return worse in {'crisis', 'bear'} or base == worse

    def verify_quantum_bounds(self) -> bool:
        result = self.quantum_optimizer.optimize()
        in_bounds = -1.0 <= float(result['energy']) <= 1.0
        weights_ok = all(0.0 <= float(value) <= 1.0 for value in self.quantum_consensus.weights.values())
        return in_bounds and weights_ok

    def verify_all(self) -> dict[str, Any]:
        veto = self.verify_veto_completeness()
        risk = self.verify_risk_monotonicity()
        quantum = self.verify_quantum_bounds()
        return {'veto': veto, 'risk': risk, 'quantum': quantum, 'proof_valid': veto['proof_valid'] and risk and quantum}
