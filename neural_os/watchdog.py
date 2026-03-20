from __future__ import annotations

import asyncio
import inspect
import time
from typing import Any

from neural_os.state_manager import StateManager


class SystemWatchdog:
    def __init__(self, event_bus: Any, state_manager: StateManager, modules: dict[str, Any], interval_seconds: float = 10.0) -> None:
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.modules = modules
        self.interval_seconds = interval_seconds
        self.restart_count = 0
        self.degraded_modules: set[str] = set()
        self._failures: dict[str, int] = {name: 0 for name in modules}
        self._circuit_state: dict[str, str] = {name: 'CLOSED' for name in modules}
        self.started_at = time.time()
        self._running = False
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if self._task is None:
            self._running = True
            self._task = asyncio.create_task(self.run(), name='system-watchdog')

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def run(self) -> None:
        self._running = True
        while self._running:
            for name, module in self.modules.items():
                await self._check_module(name, module)
            await self._auto_scale()
            await asyncio.sleep(self.interval_seconds)

    async def _check_module(self, name: str, module: Any) -> None:
        started = time.perf_counter()
        health = module.health() if hasattr(module, 'health') else {'status': 'unknown'}
        response_time_ms = health.get('response_time_ms', (time.perf_counter() - started) * 1000)
        unhealthy = health.get('status') != 'ok' or response_time_ms > 2000
        if unhealthy:
            await self.state_manager.set(f'watchdog.alert.{name}', health, ttl=3600)
            await self.event_bus.publish(f'watchdog.alert.{name}', {'module': name, 'health': health, 'timestamp': time.time()})
            self.degraded_modules.add(name)
            self._circuit_state[name] = 'OPEN'
            self._failures[name] += 1
            try:
                cls = module.__class__
                new_instance = cls(*getattr(module, '_restart_args', ()), **getattr(module, '_restart_kwargs', {}))
                if hasattr(new_instance, 'start'):
                    maybe = new_instance.start()
                    if inspect.iscoroutine(maybe):
                        await maybe
                self.modules[name] = new_instance
                self.restart_count += 1
                self._circuit_state[name] = 'HALF-OPEN'
            except Exception:
                if self._failures[name] >= 3:
                    await self.event_bus.publish('system.critical', {'module': name, 'timestamp': time.time()})
        else:
            self.degraded_modules.discard(name)
            self._failures[name] = 0
            self._circuit_state[name] = 'CLOSED'

    async def _auto_scale(self) -> None:
        cpu = 25.0
        memory = 35.0
        optimizer = self.modules.get('quantum_optimizer')
        market_data = self.modules.get('market_data')
        if cpu > 80 and optimizer is not None and hasattr(optimizer, 'tune_iterations'):
            optimizer.tune_iterations(0.5)
        if memory > 85 and market_data is not None and hasattr(market_data, 'flush_history'):
            market_data.flush_history(keep_last=100)

    def health_matrix(self) -> dict[str, Any]:
        return {name: {**(module.health() if hasattr(module, 'health') else {'status': 'unknown'}), 'circuit_breaker': self._circuit_state.get(name, 'CLOSED')} for name, module in self.modules.items()}

    def metrics(self) -> dict[str, Any]:
        return {'uptime': time.time() - self.started_at, 'restart_count': self.restart_count, 'degraded_modules': sorted(self.degraded_modules)}

    def health(self) -> dict[str, Any]:
        return {'status': 'ok', 'response_time_ms': 0.0, 'restart_count': self.restart_count}


async def main() -> None:
    from interfaces.api.dependencies import get_app_container

    container = get_app_container()
    await container.startup()
    await container.watchdog.run()


if __name__ == '__main__':
    asyncio.run(main())
