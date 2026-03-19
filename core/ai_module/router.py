from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from core.ai_module.engine import LLMEngine
from core.ai_module.memory import MemoryRecord, MemoryStore
from core.ai_module.values_core import SafetyPolicy


@dataclass(slots=True)
class ChatRequest:
    prompt: str
    session_id: str | None = None


class AIRouter:
    def __init__(self, memory_store: MemoryStore | None = None, engine: LLMEngine | None = None) -> None:
        self.memory_store = memory_store or MemoryStore()
        self.engine = engine or LLMEngine()
        self.policy = SafetyPolicy()

    async def initialize(self) -> None:
        await self.memory_store.initialize()

    async def handle_chat(self, request: ChatRequest) -> dict[str, Any]:
        session_id = request.session_id or str(uuid4())
        blocked = self.policy.check(request.prompt)
        if blocked:
            return {'session_id': session_id, 'response': blocked, 'blocked': True}

        history = await self.memory_store.get_history(session_id)
        context = [{'role': item.role, 'content': item.content} for item in history]
        await self.memory_store.add_message(MemoryRecord(session_id=session_id, role='user', content=request.prompt))
        result = await self.engine.infer(request.prompt, context=context)
        await self.memory_store.add_message(MemoryRecord(session_id=session_id, role='assistant', content=result['response']))
        return {'session_id': session_id, **result, 'blocked': False}
