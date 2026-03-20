import asyncio

from neural_os.state_manager import StateManager
from nexus.risk_manager import AutonomousRiskManager


def test_risk_manager_blocks_on_limits():
    manager = AutonomousRiskManager(StateManager())
    assessment = asyncio.run(manager.assess([], {'weights': [0.9]}, {'prices': {'DOGEUSDT': [1, 1.1]}, 'drawdown_current': 0.2, 'var_95_1h': 0.06, 'cascade_alert': {'triggered': True, 'quantum_coherence': 0.8}}))
    assert assessment['hard_blocked'] is True


def test_risk_manager_detect_regime():
    manager = AutonomousRiskManager(StateManager())
    regime = manager.detect_regime({'DOGEUSDT': [1, 1.1, 1.2, 1.3]})
    assert regime in {'bull', 'bear', 'ranging', 'crisis'}
