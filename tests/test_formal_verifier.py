from core.quantum_layer.formal_verifier import FormalVerifier
from core.quantum_layer.optimizer import QuantumOptimizer
from neural_os.state_manager import StateManager
from nexus.risk_manager import AutonomousRiskManager
from nexus.veto_logic import VetoSystem


def build_verifier():
    return FormalVerifier(VetoSystem(), AutonomousRiskManager(StateManager()), QuantumOptimizer())


def test_formal_verifier_veto_report():
    report = build_verifier().verify_veto_completeness()
    assert report['total_cases'] > 0


def test_formal_verifier_risk_monotonicity():
    assert build_verifier().verify_risk_monotonicity() is True


def test_formal_verifier_quantum_bounds():
    assert build_verifier().verify_quantum_bounds() is True


def test_formal_verifier_all():
    report = build_verifier().verify_all()
    assert 'proof_valid' in report
