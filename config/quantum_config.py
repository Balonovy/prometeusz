from dataclasses import dataclass


@dataclass(slots=True)
class QuantumConfig:
    device_name: str = 'default.qubit'
    wires: int = 4
    layers: int = 2
    shots: int | None = None
    qiskit_backend: str = 'ibmq_qasm_simulator'


DEFAULT_QUANTUM_CONFIG = QuantumConfig()
