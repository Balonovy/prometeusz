from __future__ import annotations

import asyncio
import json
from typing import Any
from urllib import error, request

from config.model_config import DEFAULT_MODEL_CONFIG
from config.settings import get_settings


class LLMEngine:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.model_config = DEFAULT_MODEL_CONFIG

    async def infer(self, prompt: str, context: list[dict[str, str]] | None = None) -> dict[str, Any]:
        payload = {
            'model': self.settings.openai_model or self.model_config.model_name,
            'messages': [*(context or []), {'role': 'user', 'content': prompt}],
            'temperature': self.model_config.temperature,
            'max_tokens': self.model_config.max_tokens,
        }
        try:
            data = await asyncio.to_thread(self._post_chat_completion, payload)
            content = data['choices'][0]['message']['content']
            return {'response': content, 'provider': self.model_config.provider, 'mode': 'remote'}
        except Exception:
            fallback = (
                'PROMETEUSZ local scaffold response: request accepted and routed successfully. '
                f'Prompt summary: {prompt[:160]}'
            )
            return {'response': fallback, 'provider': self.model_config.provider, 'mode': 'fallback'}

    def _post_chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        raw = json.dumps(payload).encode('utf-8')
        req = request.Request(
            url=f'{self.settings.openai_base_url}/chat/completions',
            data=raw,
            headers={
                'Content-Type': 'application/json',
                **({'Authorization': f'Bearer {self.settings.openai_api_key}'} if self.settings.openai_api_key else {}),
            },
            method='POST',
        )
        with request.urlopen(req, timeout=20) as response:  # noqa: S310
            body = response.read().decode('utf-8')
            return json.loads(body)
