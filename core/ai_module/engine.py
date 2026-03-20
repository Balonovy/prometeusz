from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any

from config.settings import get_settings

try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None


@dataclass(slots=True)
class ChatMessage:
    role: str
    content: str


class LLMEngine:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._calls = 0
        self._last_latency_ms = 0.0

    async def chat(self, messages: list[ChatMessage], response_format: str = 'text') -> dict[str, Any]:
        self._calls += 1
        if self.settings.mock_llm or httpx is None:
            return await self._mock_response(messages, response_format=response_format)
        payload = {
            'model': self.settings.llm_model_name,
            'messages': [{'role': message.role, 'content': message.content} for message in messages],
            'temperature': 0.2,
        }
        headers = {'Content-Type': 'application/json'}
        if self.settings.openai_api_key:
            headers['Authorization'] = f'Bearer {self.settings.openai_api_key}'
        start = asyncio.get_running_loop().time()
        async with httpx.AsyncClient(timeout=self.settings.http_timeout_seconds) as client:
            response = await client.post(f"{self.settings.openai_base_url.rstrip('/')}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        self._last_latency_ms = (asyncio.get_running_loop().time() - start) * 1000
        choice = data['choices'][0]['message']
        return {'message': choice, 'provider': self.settings.openai_base_url, 'model': data.get('model', self.settings.llm_model_name), 'usage': data.get('usage', {})}

    async def _mock_response(self, messages: list[ChatMessage], response_format: str = 'text') -> dict[str, Any]:
        start = asyncio.get_running_loop().time()
        await asyncio.sleep(0)
        latest = messages[-1].content if messages else ''
        if response_format == 'json':
            payload = self._heuristic_json(latest)
            content = json.dumps(payload)
        else:
            content = f'MOCK_RESPONSE: {latest[:200]}'
        self._last_latency_ms = (asyncio.get_running_loop().time() - start) * 1000
        return {'message': {'role': 'assistant', 'content': content}, 'provider': 'mock', 'model': 'mock-llm', 'usage': {'prompt_tokens': len(latest.split()), 'completion_tokens': len(content.split())}}

    def _heuristic_json(self, prompt: str) -> dict[str, Any]:
        pair = 'DOGEUSDT'
        action = 'HOLD'
        confidence = 0.55
        risk_level = 'medium'
        prompt_upper = prompt.upper()
        for token in prompt_upper.replace(',', ' ').split():
            if token.endswith('USDT'):
                pair = token
                break
        if 'BULL' in prompt_upper or 'BUY' in prompt_upper:
            action = 'BUY'
            confidence = 0.71
            risk_level = 'medium'
        elif 'BEAR' in prompt_upper or 'SELL' in prompt_upper:
            action = 'SELL'
            confidence = 0.69
            risk_level = 'medium'
        if 'VETO' in prompt_upper:
            action = 'HOLD'
            confidence = 0.35
            risk_level = 'high'
        return {'pair': pair, 'action': action, 'confidence': confidence, 'reasoning': 'Synthesized from mock LLM using trend, quantum score, and veto state.', 'risk_level': risk_level}

    def health(self) -> dict[str, Any]:
        return {'status': 'ok', 'response_time_ms': self._last_latency_ms, 'calls': self._calls, 'mode': 'mock' if self.settings.mock_llm or httpx is None else 'live'}
