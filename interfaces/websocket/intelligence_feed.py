from __future__ import annotations

import asyncio
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from interfaces.api.dependencies import get_app_container

router = APIRouter(tags=['intelligence-websocket'])


def _map_topic(topic: str) -> str | None:
    if topic.startswith('consciousness.perception'):
        return 'perception'
    if topic.startswith('consciousness.reasoning'):
        return 'reasoning'
    if topic.startswith('agent.decision'):
        return 'decision'
    if topic.startswith('reflection.'):
        return 'reflection'
    if topic.startswith('consciousness.learning'):
        return 'learning'
    if topic.startswith('quantum.'):
        return 'quantum'
    if topic.startswith('system.critical') or topic.startswith('watchdog.'):
        return 'watchdog'
    if topic.startswith('evolution.'):
        return 'evolution'
    if topic.startswith('neuromorphic.pattern'):
        return 'cascade'
    return None


@router.websocket('/ws/intelligence')
@router.websocket('/ws/consciousness')
async def intelligence_feed(websocket: WebSocket) -> None:
    await websocket.accept()
    container = get_app_container()
    await container.startup()
    sent = 0
    filters = {'*'}
    await websocket.send_json({'type': 'heartbeat', 'timestamp': time.time(), 'payload': {'decisions_total': container.agent.decisions_made, 'uptime': container.watchdog.metrics()['uptime']}})
    try:
        while True:
            events = container.event_bus.get_recent(limit=500)
            for event in events[sent:]:
                event_type = _map_topic(event['topic'])
                if event_type is None or ('*' not in filters and event_type not in filters):
                    continue
                await websocket.send_json({'type': event_type, 'timestamp': event['timestamp'], 'payload': event['payload']})
            sent = len(events)
            await websocket.send_json({'type': 'heartbeat', 'timestamp': time.time(), 'payload': {'decisions_total': container.agent.decisions_made, 'uptime': container.watchdog.metrics()['uptime']}})
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        return
