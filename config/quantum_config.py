from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class QuantumConfig:
    provider: str = 'simulator'
    enable_hardware: bool = False


def get_quantum_config() -> QuantumConfig:
    return QuantumConfig()
