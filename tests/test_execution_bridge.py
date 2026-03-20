import asyncio

from core.quantum_layer.quantum_rng import QuantumRNG
from neural_os.event_bus import EventBus
from neural_os.state_manager import StateManager
from nexus.execution_bridge import ExecutionBridge
from nexus.market_data import MarketDataClient


def build_bridge():
    bus = EventBus()
    market = MarketDataClient(bus)
    return ExecutionBridge(QuantumRNG(), StateManager(), bus, market)


def test_execution_bridge_submit_order():
    bridge = build_bridge()
    order = asyncio.run(bridge.submit({'pair': 'DOGEUSDT', 'action': 'BUY', 'confidence': 0.8, 'quantum_score': 0.7}, {'max_position_size': 0.25}))
    assert order['status'] == 'filled'


def test_execution_bridge_track_pnl():
    bridge = build_bridge()
    asyncio.run(bridge.submit({'pair': 'DOGEUSDT', 'action': 'BUY', 'confidence': 0.8, 'quantum_score': 0.7}, {'max_position_size': 0.25}))
    pnl = asyncio.run(bridge.track_pnl())
    assert 'total_return' in pnl


def test_execution_bridge_cancel_missing():
    bridge = build_bridge()
    result = asyncio.run(bridge.cancel('missing'))
    assert result is None
