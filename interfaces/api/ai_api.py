from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from core.ai_module.router import AIRouter, ChatRequest


router = APIRouter(prefix='/ai', tags=['ai'])
ai_router = AIRouter()


class ChatPayload(BaseModel):
    prompt: str
    session_id: str | None = None


@router.get('/health')
async def ai_health() -> dict[str, str]:
    return {'status': 'ok', 'service': 'ai'}


@router.post('/chat')
async def chat(payload: ChatPayload) -> dict[str, object]:
    return await ai_router.handle_chat(ChatRequest(prompt=payload.prompt, session_id=payload.session_id))
