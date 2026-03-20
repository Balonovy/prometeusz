import asyncio

import pytest

from core.quantum_layer.portfolio_engine import QuantumPortfolioEngine
from neural_os.event_bus import EventBus
from nexus.market_data import MarketDataClient


@pytest.fixture
def market_snapshot():
    return MarketDataClient(EventBus()).candle_snapshot()


def test_portfolio_top5_allocation(market_snapshot):
    engine = QuantumPortfolioEngine(iterations=5)
    allocation = asyncio.run(engine.optimize_live(market_snapshot))
    assert len(allocation.pairs) <= 5
    assert allocation.quantum_confidence >= 0.0


def test_portfolio_weights_sum_to_one(market_snapshot):
    engine = QuantumPortfolioEngine(iterations=5)
    allocation = asyncio.run(engine.optimize_live(market_snapshot))
    assert pytest.approx(sum(allocation.weights), rel=1e-5) == 1.0


def test_portfolio_risk_report_shape():
    engine = QuantumPortfolioEngine(iterations=5)
    report = engine.monte_carlo_risk(type('Alloc', (), {'weights': [0.6, 0.4], 'expected_return': 0.1, 'expected_volatility': 0.2})())
    assert set(report) == {'VaR_95', 'CVaR_95', 'max_drawdown', 'sharpe_ratio'}


def test_portfolio_engine_configurations_01():
    assert QuantumPortfolioEngine(risk_aversion=0.1, iterations=2).risk_aversion == 0.1


def test_portfolio_engine_configurations_03():
    assert QuantumPortfolioEngine(risk_aversion=0.3, iterations=2).risk_aversion == 0.3


def test_portfolio_engine_configurations_05():
    assert QuantumPortfolioEngine(risk_aversion=0.5, iterations=2).risk_aversion == 0.5


def test_portfolio_engine_configurations_07():
    assert QuantumPortfolioEngine(risk_aversion=0.7, iterations=2).risk_aversion == 0.7


def test_portfolio_engine_configurations_10():
    assert QuantumPortfolioEngine(risk_aversion=1.0, iterations=2).risk_aversion == 1.0
