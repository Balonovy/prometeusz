from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from interfaces.api.ai_api import router as ai_router
from interfaces.api.dependencies import get_app_container
from interfaces.api.intelligence_api import router as intelligence_router
from interfaces.api.metrics import router as metrics_router
from interfaces.api.federation_api import router as federation_router
from interfaces.api.nexus_api import router as nexus_router
from interfaces.api.quantum_api import router as quantum_router
from interfaces.websocket.intelligence_feed import router as intelligence_ws_router
from interfaces.websocket.live_feed import router as websocket_router
from nexus.dashboard_api import router as dashboard_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    container = get_app_container()
    await container.startup()
    yield
    await container.shutdown()


app = FastAPI(title='PROMETEUSZ Gateway', version='0.2.0', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
app.include_router(ai_router)
app.include_router(quantum_router)
app.include_router(nexus_router)
app.include_router(intelligence_router)
app.include_router(metrics_router)
app.include_router(federation_router)
app.include_router(dashboard_router)
app.include_router(websocket_router)
app.include_router(intelligence_ws_router)


@app.get('/health')
async def health() -> dict[str, object]:
    container = get_app_container()
    await container.startup()
    return {
        'status': 'ok',
        'modules': container.module_manager.list_modules(),
        'os': container.os_bridge.snapshot(),
        'event_bus': container.event_bus.stats(),
        'ai': container.ai_router.health(),
        'quantum': container.quantum_optimizer.health(),
        'nexus': container.market_data.health(),
        'portfolio': container.portfolio_engine.health(),
        'agent': container.agent.health(),
        'watchdog': container.watchdog.health(),
        'state_manager': container.state_manager.health(),
    }


@app.get('/system/status')
async def system_status() -> dict[str, object]:
    container = get_app_container()
    return {'status': 'ok', 'matrix': container.watchdog.health_matrix()}


@app.get('/system/metrics')
async def system_metrics() -> dict[str, object]:
    container = get_app_container()
    return {'status': 'ok', **container.watchdog.metrics()}
