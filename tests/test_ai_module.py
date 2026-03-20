import asyncio
import time

from fastapi.testclient import TestClient

from core.ai_module.adaptive_memory import AdaptiveMemory
from core.ai_module.agent import AutonomousAgent
from core.ai_module.router import AIRouter
from core.quantum_layer.optimizer import QuantumOptimizer
from interfaces.api.main import app
from neural_os.event_bus import EventBus
from neural_os.state_manager import StateManager
from nexus.market_data import MarketDataClient
from nexus.signal_engine import SignalEngine
from nexus.veto_logic import VetoSystem


def test_ai_router_returns_response() -> None:
    router = AIRouter(EventBus())
    payload = asyncio.run(router.handle_chat('test', 'Hello PROMETEUSZ'))
    assert payload['session_id'] == 'test'
    assert payload['response'].startswith('MOCK_RESPONSE:')
    assert payload['policy']['allowed'] is True


def test_ai_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get('/ai/health')
        assert response.status_code == 200
        assert response.json()['status'] == 'ok'


def test_values_policy_flow_buy() -> None:
    payload = asyncio.run(AIRouter(EventBus()).handle_chat('p', 'buy setup'))
    assert 'response' in payload


def test_values_policy_flow_sell() -> None:
    payload = asyncio.run(AIRouter(EventBus()).handle_chat('p', 'sell setup'))
    assert 'response' in payload


def test_values_policy_flow_status() -> None:
    payload = asyncio.run(AIRouter(EventBus()).handle_chat('p', 'status check'))
    assert 'response' in payload


def test_values_policy_flow_empty() -> None:
    payload = asyncio.run(AIRouter(EventBus()).handle_chat('p', 'fallback'))
    assert 'response' in payload


def test_agent_think_under_500ms() -> None:
    bus = EventBus()
    state = StateManager()
    market = MarketDataClient(bus)
    asyncio.run(market.start_once())
    engine = SignalEngine()
    engine.compute_all(market.candle_snapshot())
    agent = AutonomousAgent(bus, state, QuantumOptimizer(), engine, VetoSystem(), market, interval_seconds=0.01)
    started = time.perf_counter()
    decision = asyncio.run(agent.think({'signals': engine.compute_all(market.candle_snapshot()), 'quantum': agent.quantum_optimizer.current_market_graph_state(), 'events': []}))
    elapsed_ms = (time.perf_counter() - started) * 1000
    assert elapsed_ms < 500
    assert decision['pair'].endswith('USDT')


def test_agent_reflect_and_halt() -> None:
    bus = EventBus()
    state = StateManager()
    market = MarketDataClient(bus)
    asyncio.run(market.start_once())
    engine = SignalEngine()
    engine.compute_all(market.candle_snapshot())
    agent = AutonomousAgent(bus, state, QuantumOptimizer(), engine, VetoSystem(), market, interval_seconds=0.01)
    asyncio.run(agent.think({'signals': engine.compute_all(market.candle_snapshot()), 'quantum': agent.quantum_optimizer.current_market_graph_state(), 'events': []}))
    score = asyncio.run(agent.reflect())
    assert 0.0 <= score <= 1.0
    asyncio.run(agent.emergency_halt())
    assert agent.health()['status'] == 'halted'


def test_adaptive_memory_records_and_analyzes() -> None:
    memory = AdaptiveMemory(StateManager(), db_path='data/test_adaptive.db')
    decision = {'decision_id': '1', 'pair': 'DOGEUSDT', 'action': 'BUY', 'confidence': 0.8, 'quantum_score': 0.7, 'timestamp': 1.0}
    asyncio.run(memory.record_decision(decision, outcome=0.03))
    report = asyncio.run(memory.analyze_accuracy())
    assert report.per_pair_accuracy['DOGEUSDT'] == 1.0
    updates = asyncio.run(memory.adapt_thresholds())
    assert isinstance(updates, dict)
    insight = asyncio.run(memory.generate_insight('DOGEUSDT'))
    assert insight


def test_main_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get('/health')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'ok'
        assert 'agent' in data
