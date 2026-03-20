from __future__ import annotations

from fastapi import APIRouter

from interfaces.api.dependencies import get_app_container

router = APIRouter(prefix='/nexus', tags=['nexus'])


@router.get('/health')
async def health() -> dict[str, object]:
    container = get_app_container()
    return {'status': 'ok', 'market_data': container.market_data.health(), 'signal_engine': container.signal_engine.health(), 'veto_system': container.veto_system.health(), 'risk_manager': container.risk_manager.health()}


@router.get('/market/latest')
async def latest_market_tick() -> dict[str, object]:
    container = get_app_container()
    await container.startup()
    return container.market_data.latest_tick


@router.get('/signals')
async def signals() -> list[dict[str, object]]:
    container = get_app_container()
    signal_map = container.signal_engine.compute_all(container.market_data.candle_snapshot())
    payload = []
    for symbol, signal in signal_map.items():
        latest_candle = container.market_data.latest_candles(symbol, limit=1)[-1]
        veto = container.veto_system.evaluate(signal, latest_candle)
        await container.event_bus.publish(f'nexus.signal.{symbol}', signal)
        payload.append({**signal, 'veto': veto})
    return payload


@router.get('/risk')
async def risk() -> dict[str, object]:
    container = get_app_container()
    return container.risk_manager.current_state


@router.get('/risk/history')
async def risk_history() -> list[dict[str, object]]:
    container = get_app_container()
    return container.risk_manager.history[-100:]


@router.post('/risk/override')
async def risk_override(regime: str = 'crisis') -> dict[str, object]:
    container = get_app_container()
    container.risk_manager.set_override(regime)
    return {'status': 'ok', 'regime': regime}


@router.get('/orders')
async def orders() -> list[dict[str, object]]:
    container = get_app_container()
    return container.execution_bridge.list_orders()


@router.get('/pnl')
async def pnl() -> dict[str, object]:
    container = get_app_container()
    return await container.execution_bridge.track_pnl()


@router.get('/pnl/daily')
async def pnl_daily() -> list[dict[str, object]]:
    container = get_app_container()
    pnl = await container.execution_bridge.track_pnl()
    return [{'day': index, 'return': pnl['total_return'] / 30} for index in range(30)]


@router.post('/orders/cancel')
async def cancel_order(order_id: str = '') -> dict[str, object]:
    container = get_app_container()
    order = await container.execution_bridge.cancel(order_id)
    return {'status': 'ok' if order else 'missing', 'order': order}
