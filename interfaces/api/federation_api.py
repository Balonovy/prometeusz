from __future__ import annotations

from fastapi import APIRouter

from interfaces.api.dependencies import get_app_container

router = APIRouter(prefix='/federation', tags=['federation'])


@router.post('/params')
async def federation_params(payload: dict[str, object]) -> dict[str, object]:
    container = get_app_container()
    return await container.federated_node.receive_params(payload)


@router.get('/peers')
async def federation_peers() -> list[str]:
    container = get_app_container()
    return container.federated_node.peers


@router.post('/join')
async def federation_join(peer_url: str = 'http://peer.local') -> dict[str, object]:
    container = get_app_container()
    return container.federated_node.join(peer_url)


@router.get('/topology')
async def federation_topology() -> dict[str, object]:
    container = get_app_container()
    return container.federated_node.topology()
