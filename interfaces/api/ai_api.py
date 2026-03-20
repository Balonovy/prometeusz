from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from interfaces.api.dependencies import get_app_container

router = APIRouter(prefix='/ai', tags=['ai'])


class ChatRequest(BaseModel):
    session_id: str = Field(default='default')
    prompt: str


@router.post('/chat')
async def chat(request: ChatRequest) -> dict[str, object]:
    container = get_app_container()
    await container.startup()
    response = await container.ai_router.handle_chat(request.session_id, request.prompt)
    await container.state_manager.set(f'ai:{request.session_id}', response, ttl=3600)
    return response


@router.get('/health')
async def health() -> dict[str, object]:
    container = get_app_container()
    return {'status': 'ok', 'router': container.ai_router.health(), 'engine': container.ai_router.engine.health()}
