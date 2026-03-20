from core.quantum_layer.formal_verifier import FormalVerifier
from core.quantum_layer.optimizer import QuantumOptimizer
from core.quantum_layer.consensus import QuantumConsensus
from neural_os.state_manager import StateManager
from nexus.risk_manager import AutonomousRiskManager
from nexus.veto_logic import VetoSystem


def test_formal_verifier_all():
    verifier = FormalVerifier(VetoSystem(), AutonomousRiskManager(StateManager()), QuantumOptimizer(), QuantumConsensus())
    report = verifier.verify_all()
    assert set(report) == {'veto', 'risk', 'quantum', 'proof_valid'}


def test_formal_verifier_veto_proof():
    verifier = FormalVerifier(VetoSystem(), AutonomousRiskManager(StateManager()), QuantumOptimizer(), QuantumConsensus())
    assert verifier.verify_veto_completeness()['proof_valid'] is True
