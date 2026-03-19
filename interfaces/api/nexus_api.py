from __future__ import annotations

from fastapi import APIRouter

from nexus.dashboard_api import DashboardService
from nexus.market_data import BybitMarketDataClient


router = APIRouter(prefix='/nexus', tags=['nexus'])
market_data = BybitMarketDataClient()
dashboard_service = DashboardService(market_data)


@router.get('/health')
async def nexus_health() -> dict[str, str]:
    return {'status': 'ok', 'service': 'nexus'}


@router.get('/market')
async def market() -> dict[str, object]:
    snapshots = market_data.latest()
    return {'items': snapshots, 'count': len(snapshots)}


@router.get('/signals')
async def signals() -> dict[str, object]:
    snapshots = market_data.latest()
    return {'items': dashboard_service.build_signals(snapshots), 'count': len(snapshots)}
