from __future__ import annotations

import pytest

from neural_os.event_bus import EventBus
from neural_os.state_manager import StateManager
from nexus.autonomous_harvester import AutonomousHarvester
from nexus.market_data import BybitMarketDataClient


@pytest.mark.asyncio
async def test_autonomous_harvester_run_once_deploys_candidates() -> None:
    client = BybitMarketDataClient()
    harvester = AutonomousHarvester(
        market_data=client,
        event_bus=EventBus(),
        state_manager=StateManager(),
    )

    candidates = await harvester.run_once(chunk_size=2)

    assert len(candidates) == len(client.latest())
    assert all(candidate.symbol for candidate in candidates)
    payload = harvester.snapshot_payload()
    assert payload['total_collected'] >= len(candidates)
    assert payload['queue_size'] >= len(candidates)
