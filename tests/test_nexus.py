from nexus.dashboard_api import DashboardService
from nexus.market_data import BybitMarketDataClient


def test_nexus_dashboard_generates_signals() -> None:
    client = BybitMarketDataClient()
    dashboard = DashboardService(client)
    snapshots = client.latest()
    signals = dashboard.build_signals(snapshots)
    assert len(signals) == len(snapshots)
    assert {'symbol', 'regime', 'confidence', 'quantum_score', 'veto'} <= signals[0].keys()
