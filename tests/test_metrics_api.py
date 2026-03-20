import asyncio

from interfaces.api.dependencies import get_app_container
from interfaces.api.metrics import metrics


def test_metrics_output_contains_gauges():
    container = get_app_container()
    asyncio.run(container.startup())
    output = asyncio.run(metrics())
    assert 'prometeusz_agent_think_ms' in output
    assert 'prometeusz_portfolio_sharpe' in output
