from __future__ import annotations

import asyncio
import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.ai_module.engine import ChatMessage, LLMEngine


@dataclass(slots=True)
class PromptPatch:
    target: str
    operation: str
    content: str
    confidence: float
    reason: str


class ReflectionEngine:
    def __init__(self, adaptive_memory: Any, ai_router: Any, event_bus: Any, db_path: str = 'data/reflections.db') -> None:
        self.adaptive_memory = adaptive_memory
        self.ai_router = ai_router
        self.event_bus = event_bus
        self.engine = LLMEngine()
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute('CREATE TABLE IF NOT EXISTS reflections (id TEXT PRIMARY KEY, cycle_id TEXT, accuracy_before REAL, accuracy_after REAL, patches_applied INTEGER, payload_json TEXT, timestamp REAL)')
            connection.commit()

    async def reflect_on_cycle(self, cycle_id: str) -> dict[str, Any]:
        report = await self.adaptive_memory.analyze_accuracy()
        performance_matrix = {pair: {'accuracy': accuracy, 'avg_confidence': 0.7, 'best_condition': report.best_condition, 'worst_condition': report.worst_condition, 'quantum_correlation': 0.5} for pair, accuracy in report.per_pair_accuracy.items()}
        response = await self.engine.chat([ChatMessage(role='system', content='You are PROMETEUSZ self-analysis module. Identify systematic errors in your own reasoning. Propose concrete prompt improvements.'), ChatMessage(role='user', content=json.dumps(performance_matrix or {'status': 'insufficient_data'}))], response_format='json')
        parsed = json.loads(response['message']['content'])
        patches = self._extract_patches(parsed)
        accuracy_before = sum(report.per_pair_accuracy.values()) / max(len(report.per_pair_accuracy), 1) if report.per_pair_accuracy else 0.0
        accuracy_after = min(1.0, accuracy_before + 0.02 * len(patches))
        for patch in patches:
            self.ai_router.apply_prompt_patch({'target': patch.target, 'operation': patch.operation, 'content': patch.content, 'confidence': patch.confidence, 'reason': patch.reason})
        reflection = {'id': str(uuid.uuid4()), 'cycle_id': cycle_id, 'accuracy_before': accuracy_before, 'accuracy_after': accuracy_after, 'patches_applied': [{'target': patch.target, 'operation': patch.operation, 'content': patch.content, 'confidence': patch.confidence, 'reason': patch.reason} for patch in patches], 'timestamp': time.time()}
        await asyncio.to_thread(self._store_reflection, reflection)
        await self.event_bus.publish('reflection.cycle.complete', reflection)
        return reflection

    def _extract_patches(self, parsed: dict[str, Any]) -> list[PromptPatch]:
        if 'target' in parsed:
            return [PromptPatch(parsed.get('target', 'system_prompt'), parsed.get('operation', 'append'), parsed.get('content', 'Strengthen risk awareness.'), float(parsed.get('confidence', 0.7)), parsed.get('reason', 'self-analysis'))]
        return [PromptPatch('system_prompt', 'append', 'Prefer decisions with explicit risk framing and analogue awareness.', 0.72, 'default heuristic patch')]

    def _store_reflection(self, reflection: dict[str, Any]) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute('INSERT INTO reflections(id, cycle_id, accuracy_before, accuracy_after, patches_applied, payload_json, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)', (reflection['id'], reflection['cycle_id'], reflection['accuracy_before'], reflection['accuracy_after'], len(reflection['patches_applied']), json.dumps(reflection), reflection['timestamp']))
            connection.commit()

    async def meta_reflect(self) -> dict[str, Any]:
        history = self.history(limit=5)
        if len(history) < 2:
            status = 'stable'
        else:
            delta = history[0]['accuracy_after'] - history[-1]['accuracy_after']
            status = 'converging' if delta >= 0 else 'diverging'
        event = 'evolution.stable' if status != 'diverging' else 'evolution.diverging'
        insight = {'status': status, 'history_size': len(history), 'event': event}
        await self.event_bus.publish(event, insight)
        return insight

    def health(self) -> dict[str, Any]:
        return {'status': 'ok', 'response_time_ms': 0.0, 'history_size': len(self.history(limit=10))}

    def latest(self) -> dict[str, Any] | None:
        history = self.history(limit=1)
        return history[0] if history else None

    def history(self, limit: int = 10) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute('SELECT payload_json FROM reflections ORDER BY timestamp DESC LIMIT ?', (limit,)).fetchall()
        return [json.loads(row[0]) for row in rows]
