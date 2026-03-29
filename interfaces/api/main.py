from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.ai_module.router import AIRouter
from interfaces.api.ai_api import ai_router
from interfaces.api.ai_api import router as ai_api_router
from interfaces.api.nexus_api import market_data as nexus_market_data
from interfaces.api.nexus_api import register_harvester
from interfaces.api.nexus_api import router as nexus_api_router
from interfaces.api.quantum_api import router as quantum_api_router
from interfaces.websocket.live_feed import router as websocket_router
from neural_os.event_bus import EventBus
from neural_os.module_manager import ModuleManager
from neural_os.os_bridge import OSBridge
from neural_os.state_manager import StateManager
from nexus.autonomous_harvester import AutonomousHarvester


event_bus = EventBus()
module_manager = ModuleManager()
state_manager = StateManager()
os_bridge = OSBridge()
autonomous_harvester = AutonomousHarvester(
    market_data=nexus_market_data,
    event_bus=event_bus,
    state_manager=state_manager,
)
register_harvester(autonomous_harvester)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await ai_router.initialize()
    await nexus_market_data.start()
    await autonomous_harvester.start()
    module_manager.register('ai_module', '/ai')
    module_manager.register('quantum_layer', '/quantum')
    module_manager.register('nexus', '/nexus')
    module_manager.register('nexus_autonomous_harvester', '/nexus/autonomous/status')
    await state_manager.set_json('system:status', {'status': 'booted'})
    await event_bus.publish('system.lifecycle', {'state': 'started'})
    yield
    await autonomous_harvester.stop()
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
        'autonomous': autonomous_harvester.health(),
    }


@app.get('/')
async def root() -> dict[str, object]:
    return {
        'name': 'PROMETEUSZ',
        'services': ['ai', 'quantum', 'nexus', 'websocket', 'autonomous-harvester'],
    }
