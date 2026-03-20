import asyncio

from core.ai_module.adaptive_memory import AdaptiveMemory
from core.ai_module.federation import FederatedNode
from core.ai_module.live_learner import LiveLearner
from core.quantum_layer.quantum_rng import QuantumRNG
from neural_os.state_manager import StateManager


def build_node():
    state = StateManager()
    adaptive = AdaptiveMemory(state, db_path='data/test_federation_memory.db')
    learner = LiveLearner(adaptive, state)
    return FederatedNode(QuantumRNG(), learner, adaptive, state), learner


def test_federation_join_and_topology():
    node, _ = build_node()
    node.join('http://peer-1')
    topology = node.topology()
    assert 'http://peer-1' in topology['peers']


def test_federation_receive_params_merges():
    node, learner = build_node()
    before = learner.get_params()['signal_min_confidence']
    asyncio.run(node.receive_params({'node_id': 'peer-x', 'params': {k: v + 0.5 for k, v in learner.get_params().items()}, 'accuracy': 1.0}))
    after = learner.get_params()['signal_min_confidence']
    assert before != after
