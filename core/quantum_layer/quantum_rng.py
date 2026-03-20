from __future__ import annotations

import secrets
import uuid
from typing import Any

try:
    import pennylane as qml
    import numpy as np
except ImportError:  # pragma: no cover
    qml = None
    np = None


class QuantumRNG:
    def __init__(self) -> None:
        self.available = qml is not None

    def generate_bits(self, n: int) -> list[int]:
        if not self.available:
            return [secrets.randbits(1) for _ in range(n)]
        dev = qml.device('default.qubit', wires=n, shots=1)

        @qml.qnode(dev)
        def circuit():
            for wire in range(n):
                qml.Hadamard(wires=wire)
            return [qml.sample(qml.PauliZ(wire)) for wire in range(n)]

        measured = circuit()
        return [0 if int(value) == 1 else 1 for value in measured]

    def secure_session_id(self) -> str:
        bits = self.generate_bits(256)
        value = 0
        for bit in bits:
            value = (value << 1) | bit
        return value.to_bytes(32, 'big').hex()

    def quantum_uuid(self) -> str:
        raw = bytes.fromhex(self.secure_session_id()[:32])
        return str(uuid.UUID(bytes=raw))

    def entropy_payload(self, n: int = 16) -> dict[str, Any]:
        return {'bits': self.generate_bits(n), 'session_id': self.secure_session_id(), 'method': 'quantum' if self.available else 'fallback'}
