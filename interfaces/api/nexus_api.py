from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from nexus.autonomous_harvester import AutonomousHarvester
from nexus.dashboard_api import DashboardService
from nexus.market_data import BybitMarketDataClient


router = APIRouter(prefix='/nexus', tags=['nexus'])
market_data = BybitMarketDataClient()
dashboard_service = DashboardService(market_data)
autonomous_harvester: AutonomousHarvester | None = None


def register_harvester(harvester: AutonomousHarvester) -> None:
    global autonomous_harvester
    autonomous_harvester = harvester


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


@router.post('/autonomous/start')
async def start_autonomous() -> dict[str, object]:
    if autonomous_harvester is None:
        raise HTTPException(status_code=503, detail='autonomous harvester not registered')
    await autonomous_harvester.start()
    return {'status': 'started', 'health': autonomous_harvester.health()}


@router.post('/autonomous/stop')
async def stop_autonomous() -> dict[str, object]:
    if autonomous_harvester is None:
        raise HTTPException(status_code=503, detail='autonomous harvester not registered')
    await autonomous_harvester.stop()
    return {'status': 'stopped', 'health': autonomous_harvester.health()}


@router.get('/autonomous/status')
async def autonomous_status() -> dict[str, object]:
    if autonomous_harvester is None:
        raise HTTPException(status_code=503, detail='autonomous harvester not registered')
    return autonomous_harvester.snapshot_payload()


@router.post('/autonomous/run-once')
async def autonomous_run_once() -> dict[str, object]:
    if autonomous_harvester is None:
        raise HTTPException(status_code=503, detail='autonomous harvester not registered')
    candidates = await autonomous_harvester.run_once(chunk_size=3)
    return {
        'count': len(candidates),
        'deployable': sum(1 for candidate in candidates if candidate.verdict == 'deploy'),
        'items': [asdict(candidate) for candidate in candidates],
    }
