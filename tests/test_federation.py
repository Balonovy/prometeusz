import asyncio

from core.ai_module.adaptive_memory import AdaptiveMemory
from core.ai_module.federation import FederatedNode
from core.ai_module.live_learner import LiveLearner
from core.quantum_layer.quantum_rng import QuantumRNG
from neural_os.state_manager import StateManager


def build_node(db_path: str):
    adaptive = AdaptiveMemory(StateManager(), db_path=db_path)
    learner = LiveLearner(adaptive, StateManager())
    return FederatedNode(QuantumRNG(), learner, adaptive, StateManager()), learner, adaptive


def test_federation_join_and_topology():
    node, _, _ = build_node('data/test_fed1.db')
    node.join('http://peer-a')
    assert node.topology()['peers'] == ['http://peer-a']


def test_federation_receive_params_merges():
    node, learner, adaptive = build_node('data/test_fed2.db')
    payload = {'node_id': 'peer', 'params': {k: v + 1 for k, v in learner.get_params().items()}, 'accuracy': 0.9, 'timestamp': 0.0}
    merge = asyncio.run(node.receive_params(payload))
    assert merge['peer'] == 'peer'
