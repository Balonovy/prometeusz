import asyncio

from neural_os.event_bus import EventBus
from neural_os.state_manager import StateManager
from neural_os.watchdog import SystemWatchdog


class HealthyModule:
    def health(self):
        return {'status': 'ok', 'response_time_ms': 10}


class SlowModule:
    def __init__(self):
        self._restart_args = ()
        self._restart_kwargs = {}
    def health(self):
        return {'status': 'ok', 'response_time_ms': 2501}
    async def start(self):
        return None


class BrokenModule:
    def __init__(self):
        self._restart_args = ()
        self._restart_kwargs = {}
    def health(self):
        return {'status': 'error', 'response_time_ms': 10}
    async def start(self):
        return None


def test_watchdog_detects_slow_module():
    bus = EventBus()
    watchdog = SystemWatchdog(bus, StateManager(), {'slow': SlowModule()}, interval_seconds=0.01)
    asyncio.run(watchdog._check_module('slow', watchdog.modules['slow']))
    assert 'slow' in watchdog.degraded_modules


def test_watchdog_restart_and_metrics():
    bus = EventBus()
    watchdog = SystemWatchdog(bus, StateManager(), {'broken': BrokenModule(), 'healthy': HealthyModule()}, interval_seconds=0.01)
    asyncio.run(watchdog._check_module('broken', watchdog.modules['broken']))
    metrics = watchdog.metrics()
    assert metrics['restart_count'] >= 1


def test_watchdog_health_matrix():
    bus = EventBus()
    watchdog = SystemWatchdog(bus, StateManager(), {'healthy': HealthyModule()}, interval_seconds=0.01)
    matrix = watchdog.health_matrix()
    assert matrix['healthy']['status'] == 'ok'


def test_watchdog_circuit_breaker_defaults_1():
    modules = {f'm{idx}': HealthyModule() for idx in range(1)}
    watchdog = SystemWatchdog(EventBus(), StateManager(), modules, interval_seconds=0.01)
    assert all(item['circuit_breaker'] == 'CLOSED' for item in watchdog.health_matrix().values())


def test_watchdog_circuit_breaker_defaults_2():
    modules = {f'm{idx}': HealthyModule() for idx in range(2)}
    watchdog = SystemWatchdog(EventBus(), StateManager(), modules, interval_seconds=0.01)
    assert all(item['circuit_breaker'] == 'CLOSED' for item in watchdog.health_matrix().values())


def test_watchdog_circuit_breaker_defaults_3():
    modules = {f'm{idx}': HealthyModule() for idx in range(3)}
    watchdog = SystemWatchdog(EventBus(), StateManager(), modules, interval_seconds=0.01)
    assert all(item['circuit_breaker'] == 'CLOSED' for item in watchdog.health_matrix().values())


def test_watchdog_circuit_breaker_defaults_4():
    modules = {f'm{idx}': HealthyModule() for idx in range(4)}
    watchdog = SystemWatchdog(EventBus(), StateManager(), modules, interval_seconds=0.01)
    assert all(item['circuit_breaker'] == 'CLOSED' for item in watchdog.health_matrix().values())


def test_watchdog_circuit_breaker_defaults_5():
    modules = {f'm{idx}': HealthyModule() for idx in range(5)}
    watchdog = SystemWatchdog(EventBus(), StateManager(), modules, interval_seconds=0.01)
    assert all(item['circuit_breaker'] == 'CLOSED' for item in watchdog.health_matrix().values())
