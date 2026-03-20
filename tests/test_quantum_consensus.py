import asyncio

from core.quantum_layer.consensus import QuantumConsensus


def test_quantum_consensus_vote():
    consensus = QuantumConsensus()
    result = asyncio.run(consensus.vote([0.1, 0.2, 0.15, 0.05]))
    assert set(result) >= {'consensus_direction', 'consensus_confidence', 'agreement_ratio', 'fault_tolerance'}


def test_quantum_consensus_track_accuracy():
    consensus = QuantumConsensus()
    before = consensus.weights['circuit_vqe']
    consensus.track_accuracy('circuit_vqe', True)
    assert consensus.weights['circuit_vqe'] >= before
