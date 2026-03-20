import asyncio

from fastapi.testclient import TestClient

from core.quantum_layer.optimizer import QuantumOptimizer
from core.quantum_layer.portfolio_engine import QuantumPortfolioEngine
from core.quantum_layer.quantum_rng import QuantumRNG
from interfaces.api.main import app
from neural_os.event_bus import EventBus
from nexus.market_data import MarketDataClient


def test_quantum_optimizer_returns_vqe_result() -> None:
    result = QuantumOptimizer().optimize()
    assert result['algorithm'] == 'vqe'
    assert 'energy' in result
    assert len(result['parameters']) == 4


def test_quantum_health_endpoint() -> None:
    with TestClient(app) as client:
        assert client.get('/quantum/health').status_code == 200


def test_quantum_optimize_endpoint() -> None:
    with TestClient(app) as client:
        assert client.get('/quantum/optimize').status_code == 200


def test_quantum_portfolio_endpoint() -> None:
    with TestClient(app) as client:
        assert client.get('/quantum/portfolio').status_code == 200


def test_quantum_risk_endpoint() -> None:
    with TestClient(app) as client:
        assert client.get('/quantum/risk').status_code == 200


def test_quantum_entropy_endpoint() -> None:
    with TestClient(app) as client:
        assert client.get('/quantum/entropy').status_code == 200


def test_portfolio_engine_optimize_live() -> None:
    market = MarketDataClient(EventBus())
    engine = QuantumPortfolioEngine(iterations=5)
    allocation = asyncio.run(engine.optimize_live(market.candle_snapshot()))
    assert len(allocation.pairs) <= 5
    assert round(sum(allocation.weights), 6) in {0.0, 1.0}


def test_quantum_rng_bit_lengths_8() -> None:
    assert len(QuantumRNG().generate_bits(8)) == 8


def test_quantum_rng_bit_lengths_16() -> None:
    assert len(QuantumRNG().generate_bits(16)) == 16


def test_quantum_rng_bit_lengths_32() -> None:
    assert len(QuantumRNG().generate_bits(32)) == 32


def test_quantum_rng_bit_lengths_64() -> None:
    assert len(QuantumRNG().generate_bits(64)) == 64


def test_quantum_rng_session_shapes() -> None:
    rng = QuantumRNG()
    assert len(rng.secure_session_id()) == 64
    assert len(rng.quantum_uuid()) == 36
