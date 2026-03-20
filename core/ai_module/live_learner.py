from __future__ import annotations

import asyncio
import math
import time
from typing import Any

from core.ai_module.reflection_engine import ReflectionEngine
from neural_os.state_manager import StateManager


class LiveLearner:
    def __init__(self, adaptive_memory: Any, state_manager: StateManager, reflection_engine: ReflectionEngine | None = None) -> None:
        self.adaptive_memory = adaptive_memory
        self.state_manager = state_manager
        self.reflection_engine = reflection_engine
        self.params = {'signal_min_confidence': 0.6, 'ema_cross_weight': 1.0, 'quantum_weight': 1.0, 'veto_rsi_upper': 78.0, 'veto_rsi_lower': 22.0, 'regime_sensitivity': 1.0}
        self.rewards: list[dict[str, float]] = []
        self.cycles = 0

    def get_params(self) -> dict[str, float]:
        return dict(self.params)

    async def observe_outcome(self, decision_id: str, actual_return_1h: float) -> None:
        reward = math.tanh(actual_return_1h * 10)
        keys = list(self.params)
        target_key = keys[hash(decision_id) % len(keys)]
        old = self.params[target_key]
        sigma = 0.1
        gradient_estimate = 1.0 if reward >= 0 else -1.0
        self.params[target_key] = old + sigma * reward * gradient_estimate
        self.rewards.append({'timestamp': time.time(), 'reward': reward, 'param': target_key, 'old_value': old, 'new_value': self.params[target_key]})
        self.rewards = self.rewards[-100:]
        await self.state_manager.set('learner:params', self.params, ttl=3600)

    async def run(self) -> None:
        self.cycles += 1
        rows = await self.state_manager.list_prefix('agent:decision:', limit=10)
        for key, decision in rows:
            await self.observe_outcome(str(decision.get('decision_id', key)), float(decision.get('simulated_return', 0.01)))
        if self.reflection_engine is not None and self.cycles % 10 == 0:
            await self.reflection_engine.reflect_on_cycle(f'cycle-{self.cycles}')

    def health(self) -> dict[str, Any]:
        return {'status': 'ok', 'response_time_ms': 0.0, 'reward_events': len(self.rewards)}

    def reward_history(self) -> list[dict[str, float]]:
        return list(self.rewards)

    def convergence(self) -> dict[str, Any]:
        if len(self.rewards) < 5:
            return {'status': 'warming_up', 'avg_reward': 0.0}
        avg = sum(item['reward'] for item in self.rewards[-10:]) / min(len(self.rewards), 10)
        return {'status': 'converging' if avg >= 0 else 'diverging', 'avg_reward': avg}
