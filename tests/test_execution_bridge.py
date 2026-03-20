import asyncio

from core.quantum_layer.quantum_rng import QuantumRNG
from neural_os.event_bus import EventBus
from neural_os.state_manager import StateManager
from nexus.execution_bridge import ExecutionBridge
from nexus.market_data import MarketDataClient


def test_execution_bridge_submit_and_list():
    market = MarketDataClient(EventBus())
    bridge = ExecutionBridge(QuantumRNG(), StateManager(), EventBus(), market)
    decision = {'pair': 'DOGEUSDT', 'action': 'BUY', 'confidence': 0.8, 'quantum_score': 0.7}
    order = asyncio.run(bridge.submit(decision, {'max_position_size': 0.25}))
    assert order['symbol'] == 'DOGEUSDT'
    assert bridge.list_orders()


def test_execution_bridge_pnl_report():
    market = MarketDataClient(EventBus())
    bridge = ExecutionBridge(QuantumRNG(), StateManager(), EventBus(), market)
    asyncio.run(bridge.submit({'pair': 'DOGEUSDT', 'action': 'BUY', 'confidence': 0.8, 'quantum_score': 0.7}, {'max_position_size': 0.25}))
    pnl = asyncio.run(bridge.track_pnl())
    assert 'total_return' in pnl
