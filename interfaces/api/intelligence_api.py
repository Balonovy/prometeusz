from __future__ import annotations

from fastapi import APIRouter

from interfaces.api.dependencies import get_app_container

router = APIRouter(prefix='/intelligence', tags=['intelligence'])


@router.get('/overview')
async def overview() -> dict[str, object]:
    container = get_app_container()
    return await container.intelligence_overview()


@router.get('/master')
async def master() -> dict[str, object]:
    container = get_app_container()
    return await container.intelligence_master()


@router.get('/signals')
async def signals() -> list[dict[str, object]]:
    container = get_app_container()
    await container.startup()
    return list(container.signal_engine.compute_all(container.market_data.candle_snapshot()).values())


@router.get('/decisions')
async def decisions() -> list[object]:
    container = get_app_container()
    rows = await container.state_manager.list_prefix('agent:decision:', limit=50)
    return [value for _, value in rows][-50:]


@router.get('/quantum/portfolio')
async def quantum_portfolio() -> dict[str, object]:
    container = get_app_container()
    allocation = await container.portfolio_engine.optimize_live(container.market_data.candle_snapshot())
    return {'pairs': allocation.pairs, 'weights': allocation.weights, 'expected_return': allocation.expected_return, 'expected_volatility': allocation.expected_volatility, 'sharpe_ratio': allocation.sharpe_ratio, 'quantum_confidence': allocation.quantum_confidence}


@router.get('/reflection/latest')
async def reflection_latest() -> dict[str, object]:
    container = get_app_container()
    return container.reflection_engine.latest() or {'status': 'empty'}


@router.get('/reflection/history')
async def reflection_history() -> list[dict[str, object]]:
    container = get_app_container()
    return container.reflection_engine.history(limit=10)


@router.post('/reflection/trigger')
async def reflection_trigger() -> dict[str, object]:
    container = get_app_container()
    return await container.reflection_engine.reflect_on_cycle('manual-trigger')


@router.get('/analogues/{symbol}')
async def analogues(symbol: str) -> list[dict[str, object]]:
    container = get_app_container()
    candles = container.market_data.latest_candles(symbol, 50)
    sequence = [[float(candle.get(key, 0.0)) for key in ('open', 'high', 'low', 'close', 'volume', 'spread', 'funding_rate')] + [float(index)] for index, candle in enumerate(candles)]
    return [{'pattern_id': item.pattern_id, 'similarity': item.similarity, 'outcome_distribution': item.outcome_distribution, 'context_overlap': item.context_overlap, 'timestamp_original': item.timestamp_original} for item in container.temporal_memory.find_analogues(sequence, symbol, top_k=5, similarity_threshold=0.0)]


@router.get('/forecast/{symbol}')
async def forecast(symbol: str) -> dict[str, object]:
    container = get_app_container()
    candles = container.market_data.latest_candles(symbol, 50)
    sequence = [[float(candle.get(key, 0.0)) for key in ('open', 'high', 'low', 'close', 'volume', 'spread', 'funding_rate')] + [float(index)] for index, candle in enumerate(candles)]
    return container.temporal_memory.synthesize_forecast(container.temporal_memory.find_analogues(sequence, symbol, top_k=5, similarity_threshold=0.0))


@router.get('/features/{symbol}')
async def features(symbol: str) -> dict[str, object]:
    container = get_app_container()
    container.feature_pipeline.transform(symbol, container.market_data.latest_candles(symbol, 50))
    return container.feature_pipeline.labeled_features(symbol)


@router.get('/learner/params')
async def learner_params() -> dict[str, object]:
    container = get_app_container()
    return container.live_learner.get_params()


@router.get('/learner/reward_history')
async def learner_reward_history() -> list[dict[str, object]]:
    container = get_app_container()
    return container.live_learner.reward_history()


@router.get('/learner/convergence')
async def learner_convergence() -> dict[str, object]:
    container = get_app_container()
    return container.live_learner.convergence()


@router.post('/agent/halt')
async def agent_halt() -> dict[str, object]:
    container = get_app_container()
    await container.agent.emergency_halt()
    return {'status': 'ok', 'halted': True}


@router.get('/verify/veto')
async def verify_veto() -> dict[str, object]:
    container = get_app_container()
    return container.formal_verifier.verify_veto_completeness()


@router.get('/verify/risk')
async def verify_risk() -> dict[str, object]:
    container = get_app_container()
    return {'proof_valid': container.formal_verifier.verify_risk_monotonicity()}


@router.get('/verify/quantum')
async def verify_quantum() -> dict[str, object]:
    container = get_app_container()
    return {'proof_valid': container.formal_verifier.verify_quantum_bounds()}


@router.get('/verify/all')
async def verify_all() -> dict[str, object]:
    container = get_app_container()
    return container.formal_verifier.verify_all()
