from __future__ import annotations

import asyncio
import json
import sqlite3
from dataclasses import dataclass
from typing import Any

from config.settings import get_settings


@dataclass(slots=True)
class MemoryRecord:
    session_id: str
    role: str
    content: str


class MemoryStore:
    def __init__(self, db_path: str | None = None) -> None:
        settings = get_settings()
        self.db_path = db_path or str(settings.sqlite_path)

    async def initialize(self) -> None:
        await asyncio.to_thread(self._initialize_sync)

    def _initialize_sync(self) -> None:
        with sqlite3.connect(self.db_path) as db:
            db.execute(
                'CREATE TABLE IF NOT EXISTS conversation_memory ('
                'id INTEGER PRIMARY KEY AUTOINCREMENT, '
                'session_id TEXT NOT NULL, '
                'role TEXT NOT NULL, '
                'content TEXT NOT NULL, '
                'metadata TEXT DEFAULT "{}", '
                'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
                ')'
            )
            db.commit()

    async def add_message(self, record: MemoryRecord, metadata: dict[str, Any] | None = None) -> None:
        await asyncio.to_thread(self._add_message_sync, record, metadata or {})

    def _add_message_sync(self, record: MemoryRecord, metadata: dict[str, Any]) -> None:
        with sqlite3.connect(self.db_path) as db:
            db.execute(
                'INSERT INTO conversation_memory (session_id, role, content, metadata) VALUES (?, ?, ?, ?)',
                (record.session_id, record.role, record.content, json.dumps(metadata)),
            )
            db.commit()

    async def get_history(self, session_id: str, limit: int = 10) -> list[MemoryRecord]:
        return await asyncio.to_thread(self._get_history_sync, session_id, limit)

    def _get_history_sync(self, session_id: str, limit: int) -> list[MemoryRecord]:
        with sqlite3.connect(self.db_path) as db:
            rows = db.execute(
                'SELECT session_id, role, content FROM conversation_memory '
                'WHERE session_id = ? ORDER BY id DESC LIMIT ?',
                (session_id, limit),
            ).fetchall()
        return [MemoryRecord(*row) for row in reversed(rows)]
