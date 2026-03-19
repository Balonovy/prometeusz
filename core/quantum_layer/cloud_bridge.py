from __future__ import annotations

from dataclasses import asdict, dataclass

from config.quantum_config import DEFAULT_QUANTUM_CONFIG


@dataclass(slots=True)
class CloudBackendStatus:
    provider: str
    backend: str
    available: bool
    detail: str


class CloudBridge:
    def status(self) -> dict[str, object]:
        status = CloudBackendStatus(
            provider='IBM Quantum / D-Wave',
            backend=DEFAULT_QUANTUM_CONFIG.qiskit_backend,
            available=False,
            detail='Cloud backends are scaffolded for optional credentials; local simulation is enabled by default.',
        )
        return asdict(status)
