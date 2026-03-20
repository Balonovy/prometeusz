from __future__ import annotations

from fastapi import APIRouter, WebSocket

from interfaces.api.dependencies import get_app_container

router = APIRouter(prefix='/ws', tags=['websocket'])


@router.websocket('/live')
async def live_feed(websocket: WebSocket) -> None:
    await websocket.accept()
    container = get_app_container()
    await container.startup()
    await websocket.send_json({'latest_tick': container.market_data.latest_tick, 'signals': list(container.signal_engine.latest_signals().values())[:5]})
    await websocket.close()
