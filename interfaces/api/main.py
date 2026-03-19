from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.ai_module.router import AIRouter
from interfaces.api.ai_api import router as ai_api_router
from interfaces.api.ai_api import ai_router
from interfaces.api.nexus_api import market_data as nexus_market_data
from interfaces.api.nexus_api import router as nexus_api_router
from interfaces.api.quantum_api import router as quantum_api_router
from interfaces.websocket.live_feed import router as websocket_router
from neural_os.event_bus import EventBus
from neural_os.module_manager import ModuleManager
from neural_os.os_bridge import OSBridge
from neural_os.state_manager import StateManager


event_bus = EventBus()
module_manager = ModuleManager()
state_manager = StateManager()
os_bridge = OSBridge()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await ai_router.initialize()
    await nexus_market_data.start()
    module_manager.register('ai_module', '/ai')
    module_manager.register('quantum_layer', '/quantum')
    module_manager.register('nexus', '/nexus')
    await state_manager.set_json('system:status', {'status': 'booted'})
    await event_bus.publish('system.lifecycle', {'state': 'started'})
    yield
    await nexus_market_data.stop()


app = FastAPI(title='PROMETEUSZ Gateway', version='0.1.0', lifespan=lifespan)
app.include_router(ai_api_router)
app.include_router(quantum_api_router)
app.include_router(nexus_api_router)
app.include_router(websocket_router)


@app.get('/health')
async def health() -> dict[str, object]:
    return {
        'status': 'ok',
        'modules': module_manager.list_modules(),
        'system': os_bridge.health_snapshot(),
    }


@app.get('/')
async def root() -> dict[str, object]:
    return {'name': 'PROMETEUSZ', 'services': ['ai', 'quantum', 'nexus', 'websocket']}
