from __future__ import annotations

import json
import time
from typing import Any

from config.settings import get_settings

try:
    import redis.asyncio as redis
    from redis.exceptions import RedisError
except ImportError:  # pragma: no cover
    redis = None
    RedisError = Exception


class StateManager:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._memory: dict[str, tuple[Any, float | None]] = {}
        self._redis = redis.from_url(self.settings.redis_url, decode_responses=True) if redis is not None else None

    def _purge_expired(self) -> None:
        now = time.time()
        expired = [key for key, (_, expiry) in self._memory.items() if expiry is not None and expiry <= now]
        for key in expired:
            self._memory.pop(key, None)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        expiry = time.time() + ttl if ttl else None
        self._memory[key] = (value, expiry)
        if self._redis is not None:
            try:
                if ttl:
                    await self._redis.set(key, json.dumps(value), ex=ttl)
                else:
                    await self._redis.set(key, json.dumps(value))
            except RedisError:
                pass

    async def get(self, key: str) -> Any | None:
        self._purge_expired()
        if self._redis is not None:
            try:
                cached = await self._redis.get(key)
                if cached is not None:
                    return json.loads(cached)
            except RedisError:
                pass
        value = self._memory.get(key)
        return value[0] if value else None

    async def delete(self, key: str) -> None:
        self._memory.pop(key, None)
        if self._redis is not None:
            try:
                await self._redis.delete(key)
            except RedisError:
                pass

    async def list_prefix(self, prefix: str, limit: int = 100) -> list[tuple[str, Any]]:
        self._purge_expired()
        rows = [(key, val[0]) for key, val in self._memory.items() if key.startswith(prefix)]
        rows.sort(key=lambda item: item[0])
        return rows[-limit:]

    def health(self) -> dict[str, Any]:
        self._purge_expired()
        return {'status': 'ok', 'response_time_ms': 0.0, 'keys': len(self._memory), 'redis_enabled': self._redis is not None}
