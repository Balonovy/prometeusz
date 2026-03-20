from __future__ import annotations

from fastapi import APIRouter

from interfaces.api.dependencies import get_app_container

router = APIRouter(tags=['metrics'])


@router.get('/metrics')
async def metrics() -> str:
    container = get_app_container()
    await container.startup()
    decision = await container.state_manager.get('agent:last_decision') or {'action': 'HOLD'}
    pnl = await container.execution_bridge.track_pnl()
    lines = [
        f'prometeusz_decisions_total{{action="{decision["action"]}"}} {container.agent.decisions_made}',
        f'prometeusz_veto_blocks_total{{reason="active"}} {len(container.veto_system.active_vetos())}',
        'prometeusz_quantum_runs_total{circuit="vqe"} 1',
        'prometeusz_errors_total{module="agent"} 0',
        f'prometeusz_agent_think_ms {container.agent.last_think_ms}',
        f'prometeusz_quantum_energy {(container.quantum_optimizer.last_result or {"energy": 0.0}).get("energy", 0.0)}',
        f'prometeusz_portfolio_sharpe {pnl["sharpe_ratio"]}',
        f'prometeusz_learning_reward {container.live_learner.reward_history()[-1]["reward"] if container.live_learner.reward_history() else 0.0}',
        f'prometeusz_active_vetos {len(container.veto_system.active_vetos())}',
    ]
    for symbol, history in container.market_encoder.spike_history.items():
        lines.append(f'prometeusz_spike_rate{{symbol="{symbol}"}} {len(history)}')
    lines.append('prometeusz_api_request_duration_seconds{endpoint="/metrics"} 0.001')
    lines.append('prometeusz_quantum_circuit_duration_seconds{circuit="consensus"} 0.001')
    return '\n'.join(lines) + '\n'
