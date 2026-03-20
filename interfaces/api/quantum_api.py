from __future__ import annotations

from fastapi import APIRouter

from interfaces.api.dependencies import get_app_container

router = APIRouter(prefix='/quantum', tags=['quantum'])


@router.get('/health')
async def health() -> dict[str, object]:
    container = get_app_container()
    return {'status': 'ok', 'optimizer': container.quantum_optimizer.health(), 'portfolio': container.portfolio_engine.health(), 'consensus': container.quantum_consensus.health(), 'correlation_graph': container.correlation_graph.health()}


@router.get('/optimize')
@router.post('/optimize')
async def optimize() -> dict[str, object]:
    container = get_app_container()
    result = container.quantum_optimizer.optimize()
    await container.state_manager.set('quantum:last_run', result, ttl=3600)
    await container.event_bus.publish('quantum.optimization.complete', result)
    return result


@router.get('/portfolio')
async def portfolio() -> dict[str, object]:
    container = get_app_container()
    allocation = await container.portfolio_engine.optimize_live(container.market_data.candle_snapshot())
    payload = {'pairs': allocation.pairs, 'weights': allocation.weights, 'expected_return': allocation.expected_return, 'expected_volatility': allocation.expected_volatility, 'sharpe_ratio': allocation.sharpe_ratio, 'quantum_confidence': allocation.quantum_confidence}
    await container.event_bus.publish('quantum.portfolio.update', payload)
    return payload


@router.get('/risk')
async def risk() -> dict[str, object]:
    container = get_app_container()
    if container.portfolio_engine.last_allocation is None:
        await container.portfolio_engine.optimize_live(container.market_data.candle_snapshot())
    return container.portfolio_engine.last_risk_report or {}


@router.get('/entropy')
async def entropy() -> dict[str, object]:
    container = get_app_container()
    return container.quantum_rng.entropy_payload()


@router.get('/consensus')
async def consensus() -> dict[str, object]:
    container = get_app_container()
    features = [sum(vector[:8]) / 8 for vector in container.feature_pipeline.cache.values()][:8] or [0.0]
    return await container.quantum_consensus.vote(features)


@router.get('/consensus/weights')
async def consensus_weights() -> dict[str, object]:
    container = get_app_container()
    return container.quantum_consensus.weights


@router.get('/correlations')
async def correlations() -> dict[str, object]:
    container = get_app_container()
    matrix = container.correlation_graph.build_correlation_matrix(container.market_data.candle_snapshot())
    graph_state = container.correlation_graph.encode_as_graph_state(matrix)
    return {'matrix': matrix, 'graph_state': graph_state}


@router.get('/cascade')
async def cascade() -> dict[str, object]:
    container = get_app_container()
    matrix = container.correlation_graph.build_correlation_matrix(container.market_data.candle_snapshot())
    graph_state = container.correlation_graph.encode_as_graph_state(matrix)
    return container.correlation_graph.detect_cascade(graph_state, sorted(container.market_data.candle_snapshot()))


@router.get('/hardware/status')
async def hardware_status() -> dict[str, object]:
    container = get_app_container()
    return container.cloud_bridge.status()


@router.get('/hardware/jobs')
async def hardware_jobs() -> list[dict[str, object]]:
    container = get_app_container()
    return container.cloud_bridge.recent_jobs()
