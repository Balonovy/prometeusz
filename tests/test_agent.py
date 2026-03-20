import asyncio
import time
import tracemalloc

from core.ai_module.agent import AutonomousAgent
from core.quantum_layer.optimizer import QuantumOptimizer
from neural_os.event_bus import EventBus
from neural_os.state_manager import StateManager
from nexus.market_data import MarketDataClient
from nexus.signal_engine import SignalEngine
from nexus.veto_logic import VetoSystem


def build_agent():
    bus = EventBus()
    state = StateManager()
    market = MarketDataClient(bus)
    asyncio.run(market.start_once())
    engine = SignalEngine()
    engine.compute_all(market.candle_snapshot())
    agent = AutonomousAgent(bus, state, QuantumOptimizer(), engine, VetoSystem(), market, interval_seconds=0.01)
    return agent, bus, state, market, engine


def test_agent_happy_path():
    agent, bus, state, market, engine = build_agent()
    decision = asyncio.run(agent.think({'signals': engine.compute_all(market.candle_snapshot()), 'quantum': agent.quantum_optimizer.current_market_graph_state(), 'events': []}))
    assert decision['action'] in {'BUY', 'SELL', 'HOLD'}
    assert bus.poll_events('agent.decision')
    stored = asyncio.run(state.get(f"agent:decision:{decision['decision_id']}"))
    assert stored['pair'] == decision['pair']


def test_agent_run_and_stop():
    agent, _, _, _, _ = build_agent()

    async def runner():
        task = asyncio.create_task(agent.run())
        await asyncio.sleep(0.03)
        await agent.stop()
        task.cancel()

    asyncio.run(runner())
    assert agent.decisions_made >= 1


def test_agent_performance_and_memory():
    agent, _, _, market, engine = build_agent()
    tracemalloc.start()
    start = time.perf_counter()
    for _ in range(100):
        asyncio.run(agent.think({'signals': engine.compute_all(market.candle_snapshot()), 'quantum': agent.quantum_optimizer.current_market_graph_state(), 'events': []}))
    elapsed_ms = (time.perf_counter() - start) * 1000 / 100
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert elapsed_ms < 500
    assert peak - current < 3_000_000


def test_agent_reflection_score():
    agent, _, _, market, engine = build_agent()
    asyncio.run(agent.think({'signals': engine.compute_all(market.candle_snapshot()), 'quantum': agent.quantum_optimizer.current_market_graph_state(), 'events': []}))
    score = asyncio.run(agent.reflect())
    assert 0.0 <= score <= 1.0


def test_agent_emergency_halt_publishes_event():
    agent, bus, _, _, _ = build_agent()
    asyncio.run(agent.emergency_halt())
    assert bus.poll_events('agent.halt')
