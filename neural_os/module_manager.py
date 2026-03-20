from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ModuleDescriptor:
    name: str
    health: str


class ModuleManager:
    def __init__(self) -> None:
        self.modules = [
            ModuleDescriptor(name='ai_module', health='ready'),
            ModuleDescriptor(name='quantum_layer', health='ready'),
            ModuleDescriptor(name='nexus', health='ready'),
            ModuleDescriptor(name='agent', health='ready'),
            ModuleDescriptor(name='watchdog', health='ready'),
            ModuleDescriptor(name='neuromorphic', health='ready'),
        ]

    def list_modules(self) -> list[dict[str, str]]:
        return [{'name': descriptor.name, 'health': descriptor.health} for descriptor in self.modules]
