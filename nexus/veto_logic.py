from __future__ import annotations


class VetoLogic:
    def evaluate(self, signal: dict[str, float | str], funding_rate: float) -> dict[str, str | bool]:
        blocked = funding_rate > 0.003 and signal['regime'] == 'bullish'
        return {
            'status': 'VETO' if blocked else 'CLEAR',
            'allowed': not blocked,
            'reason': 'Funding rate too elevated for long exposure.' if blocked else 'Conditions acceptable.',
        }
