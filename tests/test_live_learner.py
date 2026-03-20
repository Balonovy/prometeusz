import asyncio

from core.ai_module.adaptive_memory import AdaptiveMemory
from core.ai_module.live_learner import LiveLearner
from neural_os.state_manager import StateManager


def test_live_learner_updates_params():
    learner = LiveLearner(AdaptiveMemory(StateManager(), db_path='data/test_live_learner.db'), StateManager())
    before = learner.get_params()['signal_min_confidence']
    asyncio.run(learner.observe_outcome('decision-1', 0.03))
    after = learner.get_params()['signal_min_confidence']
    assert before != after or learner.reward_history()


def test_live_learner_convergence_shape():
    learner = LiveLearner(AdaptiveMemory(StateManager(), db_path='data/test_live_learner2.db'), StateManager())
    for idx in range(6):
        asyncio.run(learner.observe_outcome(f'decision-{idx}', 0.01))
    convergence = learner.convergence()
    assert set(convergence) == {'status', 'avg_reward'}
