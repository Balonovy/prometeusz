from __future__ import annotations

from typing import Any

from core.ai_module.engine import ChatMessage, LLMEngine
from core.ai_module.memory import MemoryRecord, MemoryStore
from core.ai_module.values_core import ValuesCore
from neural_os.event_bus import EventBus


class AIRouter:
    def __init__(self, event_bus: EventBus) -> None:
        self.engine = LLMEngine()
        self.memory = MemoryStore()
        self.values = ValuesCore()
        self.event_bus = event_bus
        self._last_response: dict[str, Any] | None = None
        self.system_prompt = 'You are PROMETEUSZ assistant.'

    async def handle_chat(self, session_id: str, prompt: str) -> dict[str, Any]:
        evaluation = self.values.evaluate(prompt)
        messages = [ChatMessage(role='system', content=self.system_prompt), ChatMessage(role='user', content=evaluation['transformed_prompt'])]
        result = await self.engine.chat(messages)
        payload = {'session_id': session_id, 'prompt': prompt, 'response': result['message']['content'], 'policy': evaluation, 'provider': result['provider'], 'system_prompt': self.system_prompt}
        self._last_response = payload
        await self.memory.append(MemoryRecord(session_id=session_id, payload=payload))
        await self.event_bus.publish('ai.responses', payload)
        return payload

    def apply_prompt_patch(self, patch: dict[str, Any]) -> None:
        operation = patch.get('operation', 'append')
        content = patch.get('content', '')
        if operation == 'replace':
            self.system_prompt = content
        elif operation == 'strengthen':
            self.system_prompt = f'{self.system_prompt} IMPORTANT: {content}'
        else:
            self.system_prompt = f'{self.system_prompt} {content}'.strip()

    def health(self) -> dict[str, Any]:
        return {'status': 'ok', 'response_time_ms': self.engine.health()['response_time_ms'], 'last_response': self._last_response is not None, 'system_prompt_length': len(self.system_prompt)}
