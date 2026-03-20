from __future__ import annotations

import time
from typing import Any

try:
    import aiohttp
except ImportError:  # pragma: no cover
    aiohttp = None


class FederatedNode:
    def __init__(self, quantum_rng: Any, live_learner: Any, adaptive_memory: Any, state_manager: Any) -> None:
        self.quantum_rng = quantum_rng
        self.live_learner = live_learner
        self.adaptive_memory = adaptive_memory
        self.state_manager = state_manager
        self.node_id = quantum_rng.secure_session_id()
        self.peers: list[str] = []
        self.merges: list[dict[str, Any]] = []

    async def broadcast_params(self) -> list[dict[str, Any]]:
        local_params = self.live_learner.get_params()
        payload = {'node_id': self.node_id, 'params': {k: v + 0.1 for k, v in local_params.items()}, 'accuracy': 1.0, 'n_decisions': len(await self.adaptive_memory.decision_history(100)), 'timestamp': time.time()}
        results = []
        if aiohttp is not None:
            for peer_url in self.peers:
                async with aiohttp.ClientSession() as session:
                    try:
                        await session.post(f'{peer_url}/federation/params', json=payload, timeout=5)
                        results.append({'peer': peer_url, 'status': 'sent'})
                    except Exception:
                        results.append({'peer': peer_url, 'status': 'failed'})
        return results

    async def receive_params(self, payload: dict[str, Any]) -> dict[str, Any]:
        local_params = self.live_learner.get_params()
        local_accuracy = 1.0
        peer_accuracy = float(payload.get('accuracy', 1.0))
        weight = peer_accuracy / (local_accuracy + peer_accuracy)
        merged = {key: (1 - weight) * local_params[key] + weight * float(payload['params'][key]) for key in local_params}
        self.live_learner.params = merged
        record = {'peer': payload['node_id'], 'weight': weight, 'timestamp': time.time()}
        self.merges.append(record)
        await self.state_manager.set('federation:last_merge', record, ttl=3600)
        return record

    def join(self, peer_url: str) -> dict[str, Any]:
        if peer_url not in self.peers:
            self.peers.append(peer_url)
        return {'joined': peer_url, 'peers': self.peers}

    def topology(self) -> dict[str, Any]:
        return {'node_id': self.node_id, 'peers': list(self.peers), 'merges': list(self.merges[-20:])}

    def health(self) -> dict[str, Any]:
        return {'status': 'ok', 'response_time_ms': 0.0, 'peers': len(self.peers)}
