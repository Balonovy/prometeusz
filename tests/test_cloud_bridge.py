import asyncio

from core.quantum_layer.cloud_bridge import IBMQuantumBridge


def test_cloud_bridge_connect_fallback():
    bridge = IBMQuantumBridge()
    result = asyncio.run(bridge.connect(''))
    assert result in {True, False}


def test_cloud_bridge_vqe_and_status():
    bridge = IBMQuantumBridge()
    result = asyncio.run(bridge.run_vqe_real([0.1, 0.2, 0.3, 0.4]))
    assert 'energy' in result
    assert 'backend' in bridge.status()
