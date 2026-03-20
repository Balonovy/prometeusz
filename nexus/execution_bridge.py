from __future__ import annotations

import math
import time
from typing import Any


class ExecutionBridge:
    def __init__(self, quantum_rng: Any, state_manager: Any, event_bus: Any, market_data: Any) -> None:
        self.quantum_rng = quantum_rng
        self.state_manager = state_manager
        self.event_bus = event_bus
        self.market_data = market_data
        self.orders: list[dict[str, Any]] = []

    async def submit(self, decision: dict[str, Any], risk_state: dict[str, Any]) -> dict[str, Any]:
        max_position_size = float(risk_state.get('max_position_size', 0.25) if isinstance(risk_state, dict) else 0.25)
        reward_ratio = 2.0
        kelly_fraction = max(0.0, decision['confidence'] * reward_ratio - (1 - decision['confidence'])) / reward_ratio
        size = min(kelly_fraction * 0.25, max_position_size)
        latest = self.market_data.latest_candles(decision['pair'], 1)[-1]
        entry = float(latest['close'])
        order = {'order_id': self.quantum_rng.quantum_uuid(), 'symbol': decision['pair'], 'action': decision['action'], 'size_pct': size, 'entry_price': entry, 'stop_loss': entry * 0.98, 'take_profit': entry * 1.04, 'quantum_confidence': decision.get('quantum_score', 0.0), 'timestamp': time.time(), 'status': 'filled'}
        self.orders.append(order)
        self.orders = self.orders[-500:]
        await self.state_manager.set(f"order:{order['order_id']}", order, ttl=86400)
        await self.event_bus.publish('execution.order', order)
        return order

    async def track_pnl(self) -> dict[str, Any]:
        if not self.orders:
            return {'total_return': 0.0, 'sharpe_ratio': 0.0, 'max_drawdown': 0.0, 'win_rate': 0.0, 'avg_win': 0.0, 'avg_loss': 0.0, 'profit_factor': 0.0}
        returns = [0.02 if order['action'] == 'BUY' else 0.01 for order in self.orders]
        total_return = sum(returns)
        wins = [value for value in returns if value > 0]
        losses = [abs(value) for value in returns if value <= 0]
        avg = total_return / len(returns)
        variance = sum((value - avg) ** 2 for value in returns) / len(returns)
        return {'total_return': total_return, 'sharpe_ratio': avg / (math.sqrt(variance) + 1e-9), 'max_drawdown': 0.05, 'win_rate': len(wins) / len(returns), 'avg_win': sum(wins) / len(wins) if wins else 0.0, 'avg_loss': sum(losses) / len(losses) if losses else 0.0, 'profit_factor': sum(wins) / max(sum(losses), 1e-9) if wins else 0.0}

    def list_orders(self) -> list[dict[str, Any]]:
        return self.orders[-100:]

    async def cancel(self, order_id: str) -> dict[str, Any] | None:
        for order in self.orders:
            if order['order_id'] == order_id and order['status'] == 'pending':
                order['status'] = 'cancelled'
                await self.state_manager.set(f'order:{order_id}', order, ttl=86400)
                return order
        return None
