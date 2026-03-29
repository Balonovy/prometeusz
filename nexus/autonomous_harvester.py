"""
nexus/autonomous_harvester.py
Autonomiczny silnik ciągłego zbierania, oceny i wdrażania kandydatów sygnałów.
"""
from __future__ import annotations

import asyncio
import contextlib
import time
from dataclasses import asdict, dataclass, field
from typing import Literal

from neural_os.event_bus import EventBus
from neural_os.state_manager import StateManager
from nexus.market_data import BybitMarketDataClient


@dataclass(slots=True)
class EvaluationCriteria:
    min_liquidity: float = 150_000.0
    max_funding_rate: float = 0.003
    min_quality_score: float = 0.65
    min_momentum: float = 0.001


@dataclass(slots=True)
class Candidate:
    symbol: str
    quality_score: float
    momentum_score: float
    liquidity_score: float
    risk_score: float
    verdict: Literal['deploy', 'watch', 'reject']
    reason: str
    timestamp: float


@dataclass(slots=True)
class HarvestSnapshot:
    status: Literal['idle', 'running', 'stopped']
    cycle: int
    total_collected: int
    total_deployed: int
    queue_size: int
    last_candidates: list[Candidate] = field(default_factory=list)


class AutonomousHarvester:
    def __init__(
        self,
        market_data: BybitMarketDataClient,
        event_bus: EventBus,
        state_manager: StateManager,
        criteria: EvaluationCriteria | None = None,
    ) -> None:
        self._market_data = market_data
        self._event_bus = event_bus
        self._state_manager = state_manager
        self._criteria = criteria or EvaluationCriteria()
        self._task: asyncio.Task[None] | None = None
        self._running = False
        self._cycle = 0
        self._total_collected = 0
        self._total_deployed = 0
        self._queue: asyncio.Queue[Candidate] = asyncio.Queue()
        self._last_candidates: list[Candidate] = []

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._running = True
        await self._state_manager.set_json('module:autonomous_harvester', {'status': 'ok'})
        await self._event_bus.publish('nexus.harvester.lifecycle', {'state': 'started'})
        self._task = asyncio.create_task(self._loop(), name='nexus-autonomous-harvester')

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        await self._state_manager.set_json('module:autonomous_harvester', {'status': 'stopped'})
        await self._event_bus.publish('nexus.harvester.lifecycle', {'state': 'stopped'})

    async def _loop(self) -> None:
        while self._running:
            self._cycle += 1
            candidates = await self.collect_and_score_once()
            await self._process_in_chunks(candidates, chunk_size=2)
            await asyncio.sleep(2)

    async def run_once(self, chunk_size: int = 3) -> list[Candidate]:
        candidates = await self.collect_and_score_once()
        await self._process_in_chunks(candidates, chunk_size=chunk_size)
        return candidates

    async def collect_and_score_once(self) -> list[Candidate]:
        snapshots = self._market_data.latest()
        evaluated = [self._evaluate_snapshot(snapshot) for snapshot in snapshots]
        self._total_collected += len(evaluated)
        self._last_candidates = evaluated[:10]
        await self._event_bus.publish(
            'nexus.harvester.collected',
            {
                'cycle': self._cycle,
                'count': len(evaluated),
                'deployable': sum(1 for item in evaluated if item.verdict == 'deploy'),
            },
        )
        return evaluated

    def _evaluate_snapshot(self, snapshot: dict[str, float | str]) -> Candidate:
        price = float(snapshot['price'])
        turnover_24h = float(snapshot['turnover_24h'])
        funding_rate = abs(float(snapshot['funding_rate']))
        momentum_score = min(max((price % 10) / 10, 0.0), 1.0)
        liquidity_score = min(turnover_24h / max(self._criteria.min_liquidity * 2, 1.0), 1.0)
        funding_component = max(0.0, 1.0 - funding_rate / max(self._criteria.max_funding_rate, 0.0001))
        quality_score = round((momentum_score * 0.45) + (liquidity_score * 0.40) + (funding_component * 0.15), 4)
        risk_score = round(1.0 - funding_component, 4)
        verdict = self._decide(quality_score=quality_score, momentum_score=momentum_score, funding_rate=funding_rate)
        reason = f"quality={quality_score}, momentum={round(momentum_score, 4)}, funding={round(funding_rate, 6)}"
        return Candidate(
            symbol=str(snapshot['symbol']),
            quality_score=quality_score,
            momentum_score=round(momentum_score, 4),
            liquidity_score=round(liquidity_score, 4),
            risk_score=risk_score,
            verdict=verdict,
            reason=reason,
            timestamp=time.time(),
        )

    def _decide(self, quality_score: float, momentum_score: float, funding_rate: float) -> Literal['deploy', 'watch', 'reject']:
        if (
            quality_score >= self._criteria.min_quality_score
            and momentum_score >= self._criteria.min_momentum
            and funding_rate <= self._criteria.max_funding_rate
        ):
            return 'deploy'
        if quality_score >= self._criteria.min_quality_score * 0.8:
            return 'watch'
        return 'reject'

    async def _process_in_chunks(self, candidates: list[Candidate], chunk_size: int) -> None:
        for idx in range(0, len(candidates), chunk_size):
            chunk = candidates[idx : idx + chunk_size]
            for candidate in chunk:
                await self._queue.put(candidate)
            await self._deploy_chunk(chunk)

    async def _deploy_chunk(self, chunk: list[Candidate]) -> None:
        deployable = [candidate for candidate in chunk if candidate.verdict == 'deploy']
        if deployable:
            self._total_deployed += len(deployable)
            await self._event_bus.publish(
                'nexus.harvester.deployed',
                {'count': len(deployable), 'symbols': [candidate.symbol for candidate in deployable]},
            )
        await self._state_manager.set_json(
            'nexus:harvester:last_chunk',
            {'count': len(chunk), 'deployable': len(deployable)},
        )

    def snapshot(self) -> HarvestSnapshot:
        return HarvestSnapshot(
            status='running' if self._running else 'stopped' if self._cycle > 0 else 'idle',
            cycle=self._cycle,
            total_collected=self._total_collected,
            total_deployed=self._total_deployed,
            queue_size=self._queue.qsize(),
            last_candidates=self._last_candidates,
        )

    def health(self) -> dict[str, str | int]:
        return {
            'status': 'ok' if self._running else 'degraded',
            'cycle': self._cycle,
            'queue_size': self._queue.qsize(),
        }

    def snapshot_payload(self) -> dict[str, object]:
        snapshot = self.snapshot()
        return {
            'status': snapshot.status,
            'cycle': snapshot.cycle,
            'total_collected': snapshot.total_collected,
            'total_deployed': snapshot.total_deployed,
            'queue_size': snapshot.queue_size,
            'last_candidates': [asdict(candidate) for candidate in snapshot.last_candidates],
        }
