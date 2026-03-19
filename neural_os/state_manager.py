from __future__ import annotations

import json
from typing import Any

try:
    import redis.asyncio as redis
except Exception:  # pragma: no cover
    redis = None

from config.settings import get_settings


class StateManager:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._memory_store: dict[str, Any] = {}
        self._redis = redis.from_url(self.settings.redis_url, decode_responses=True) if redis else None

    async def set_json(self, key: str, value: dict[str, Any]) -> None:
        self._memory_store[key] = value
        if self._redis:
            try:
                await self._redis.set(key, json.dumps(value))
            except Exception:
                pass

    async def get_json(self, key: str) -> dict[str, Any] | None:
        if self._redis:
            try:
                value = await self._redis.get(key)
                if value:
                    return json.loads(value)
            except Exception:
                pass
        return self._memory_store.get(key)
