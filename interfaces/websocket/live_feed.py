from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from nexus.dashboard_api import DashboardService
from nexus.market_data import BybitMarketDataClient


router = APIRouter(prefix='/ws', tags=['websocket'])
_market_data = BybitMarketDataClient()
_dashboard = DashboardService(_market_data)


@router.websocket('/live')
async def live_feed(websocket: WebSocket) -> None:
    await websocket.accept()
    await _market_data.start()
    try:
        while True:
            payload = {
                'market': _market_data.latest(),
                'signals': _dashboard.build_signals(_market_data.latest()),
            }
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        return
