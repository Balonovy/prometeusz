from __future__ import annotations

import asyncio
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from config.settings import get_settings

try:
    import redis.asyncio as redis
    from redis.exceptions import RedisError
except ImportError:  # pragma: no cover
    redis = None
    RedisError = Exception


@dataclass(slots=True)
class MemoryRecord:
    session_id: str
    payload: dict[str, Any]


class MemoryStore:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.db_path = Path(self.settings.sqlite_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_sqlite()
        self._redis = redis.from_url(self.settings.redis_url, decode_responses=True) if redis is not None else None

    def _init_sqlite(self) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute('CREATE TABLE IF NOT EXISTS memory (session_id TEXT NOT NULL, payload TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            connection.commit()

    async def append(self, record: MemoryRecord) -> None:
        await asyncio.to_thread(self._append_sqlite, record)
        if self._redis is not None:
            try:
                await self._redis.set(f'memory:{record.session_id}', json.dumps(record.payload))
            except RedisError:
                pass

    def _append_sqlite(self, record: MemoryRecord) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute('INSERT INTO memory(session_id, payload) VALUES (?, ?)', (record.session_id, json.dumps(record.payload)))
            connection.commit()

    async def latest(self, session_id: str) -> dict[str, Any] | None:
        if self._redis is not None:
            try:
                cached = await self._redis.get(f'memory:{session_id}')
                if cached:
                    return json.loads(cached)
            except RedisError:
                pass
        return await asyncio.to_thread(self._latest_sqlite, session_id)

    def _latest_sqlite(self, session_id: str) -> dict[str, Any] | None:
        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute('SELECT payload FROM memory WHERE session_id = ? ORDER BY created_at DESC LIMIT 1', (session_id,)).fetchone()
        return json.loads(row[0]) if row else None
