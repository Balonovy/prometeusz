from __future__ import annotations

from fastapi import APIRouter

from interfaces.api.dependencies import get_app_container

router = APIRouter(prefix='/dashboard', tags=['dashboard'])


@router.get('/status')
async def dashboard_status() -> dict[str, object]:
    container = get_app_container()
    await container.startup()
    return {'latest_tick': container.market_data.latest_tick, 'signals': list(container.signal_engine.latest_signals().values())[:5], 'event_bus_stats': container.event_bus.stats()}
