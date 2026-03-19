from core.quantum_layer.finance_qml import QuantumFinanceModel
from core.quantum_layer.simulator import QuantumSimulator


def test_quantum_vqe_runs() -> None:
    result = QuantumSimulator().run_vqe(steps=3)
    assert len(result.parameters) == 8
    assert len(result.expectation_z) == 4
    assert -1.0 <= result.energy <= 1.0


def test_quantum_portfolio_demo() -> None:
    result = QuantumFinanceModel().optimize_demo_portfolio()
    assert sum(result.selection) <= 2
    assert isinstance(result.score, float)
