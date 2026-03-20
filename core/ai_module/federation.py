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

    async def broadcast_params(self) -> None:
        local_params = self.live_learner.get_params()
        epsilon = 0.1
        noisy_params = {key: value + ((hash((self.node_id, key)) % 100) / 1000 - epsilon / 2) for key, value in local_params.items()}
        accuracy_report = await self.adaptive_memory.analyze_accuracy()
        overall = sum(accuracy_report.per_pair_accuracy.values()) / max(len(accuracy_report.per_pair_accuracy), 1) if accuracy_report.per_pair_accuracy else 0.5
        payload = {'node_id': self.node_id, 'params': noisy_params, 'accuracy': overall, 'n_decisions': len(await self.adaptive_memory.decision_history(limit=1000)), 'timestamp': time.time()}
        await self.state_manager.set('federation:last_broadcast', payload, ttl=3600)
        if aiohttp is None:
            return
        for peer_url in self.peers:
            async with aiohttp.ClientSession() as session:
                await session.post(f'{peer_url}/federation/params', json=payload, timeout=5)

    async def receive_params(self, payload: dict[str, Any]) -> dict[str, Any]:
        local_accuracy_report = await self.adaptive_memory.analyze_accuracy()
        local_accuracy = sum(local_accuracy_report.per_pair_accuracy.values()) / max(len(local_accuracy_report.per_pair_accuracy), 1) if local_accuracy_report.per_pair_accuracy else 0.5
        peer_accuracy = float(payload['accuracy'])
        peer_params = payload['params']
        local_params = self.live_learner.get_params()
        weight = peer_accuracy / max(local_accuracy + peer_accuracy, 1e-9)
        merged = {key: (1 - weight) * local_params[key] + weight * peer_params[key] for key in local_params}
        self.live_learner.params.update(merged)
        merge_event = {'peer': payload['node_id'], 'weight': weight, 'timestamp': time.time()}
        self.merges.append(merge_event)
        self.merges = self.merges[-100:]
        await self.state_manager.set('federation:last_merge', merge_event, ttl=3600)
        return merge_event

    def join(self, peer_url: str) -> dict[str, Any]:
        if peer_url not in self.peers:
            self.peers.append(peer_url)
        return {'node_id': self.node_id, 'peers': self.peers}

    def topology(self) -> dict[str, Any]:
        return {'node_id': self.node_id, 'peers': list(self.peers), 'merges': self.merges[-10:]}
