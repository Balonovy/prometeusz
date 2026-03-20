from __future__ import annotations

from fastapi import APIRouter

from interfaces.api.dependencies import get_app_container

router = APIRouter(tags=['metrics'])


@router.get('/metrics')
async def metrics() -> str:
    container = get_app_container()
    master = await container.intelligence_master()
    veto_count = len(master['market']['active_vetos'])
    sharpe = master['quantum']['portfolio']['sharpe_ratio']
    reward = master['agent']['learning_reward_avg']
    lines = [
        '# TYPE prometeusz_decisions_total counter',
        f"prometeusz_decisions_total{{action=\"{master['agent']['last_decision'].get('action', 'HOLD')}\"}} {master['agent']['decisions_1h']}",
        '# TYPE prometeusz_active_vetos gauge',
        f'prometeusz_active_vetos {veto_count}',
        '# TYPE prometeusz_portfolio_sharpe gauge',
        f'prometeusz_portfolio_sharpe {sharpe}',
        '# TYPE prometeusz_learning_reward gauge',
        f'prometeusz_learning_reward {reward}',
        '# TYPE prometeusz_agent_think_ms gauge',
        f"prometeusz_agent_think_ms {master['agent']['cognitive_load_ms']}",
    ]
    return "\n".join(lines) + "\n"
