from __future__ import annotations

from dataclasses import MISSING, dataclass, fields, is_dataclass, make_dataclass
from typing import Any


class BaseModel:
    def __init__(self, **kwargs: Any) -> None:
        annotations = getattr(self, '__annotations__', {})
        for name in annotations:
            if name in kwargs:
                setattr(self, name, kwargs[name])
            elif hasattr(self.__class__, name):
                setattr(self, name, getattr(self.__class__, name))
            else:
                raise TypeError(f'Missing field: {name}')

    def dict(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in getattr(self, '__annotations__', {})}


def Field(default: Any = MISSING, **_: Any) -> Any:
    return default if default is not MISSING else None
