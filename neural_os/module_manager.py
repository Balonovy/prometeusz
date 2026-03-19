from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ModuleRegistration:
    name: str
    status: str
    endpoint: str


class ModuleManager:
    def __init__(self) -> None:
        self._modules: dict[str, ModuleRegistration] = {}

    def register(self, name: str, endpoint: str, status: str = 'ready') -> None:
        self._modules[name] = ModuleRegistration(name=name, endpoint=endpoint, status=status)

    def list_modules(self) -> list[dict[str, str]]:
        return [registration.__dict__ for registration in self._modules.values()]
