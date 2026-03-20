import asyncio

from core.ai_module.adaptive_memory import AdaptiveMemory
from core.ai_module.reflection_engine import ReflectionEngine
from core.ai_module.router import AIRouter
from neural_os.event_bus import EventBus
from neural_os.state_manager import StateManager


def test_reflection_engine_trigger_cycle():
    memory = AdaptiveMemory(StateManager(), db_path='data/test_reflection_memory.db')
    for idx in range(3):
        asyncio.run(memory.record_decision({'decision_id': str(idx), 'pair': 'DOGEUSDT', 'action': 'BUY', 'confidence': 0.7, 'quantum_score': 0.6, 'timestamp': float(idx)}, outcome=0.02))
    engine = ReflectionEngine(memory, AIRouter(EventBus()), EventBus(), db_path='data/test_reflections.db')
    report = asyncio.run(engine.reflect_on_cycle('cycle-1'))
    assert report['cycle_id'] == 'cycle-1'
    assert report['patches_applied']


def test_reflection_engine_meta_reflect():
    memory = AdaptiveMemory(StateManager(), db_path='data/test_reflection_memory2.db')
    asyncio.run(memory.record_decision({'decision_id': '1', 'pair': 'DOGEUSDT', 'action': 'BUY', 'confidence': 0.7, 'quantum_score': 0.6, 'timestamp': 1.0}, outcome=0.02))
    event_bus = EventBus()
    engine = ReflectionEngine(memory, AIRouter(event_bus), event_bus, db_path='data/test_reflections2.db')
    asyncio.run(engine.reflect_on_cycle('cycle-a'))
    meta = asyncio.run(engine.meta_reflect())
    assert meta['status'] in {'stable', 'converging', 'diverging'}
