from __future__ import annotations

import asyncio
import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.ai_module.engine import ChatMessage, LLMEngine
from neural_os.state_manager import StateManager


@dataclass(slots=True)
class AccuracyReport:
    per_pair_accuracy: dict[str, float]
    per_action_accuracy: dict[str, float]
    confidence_calibration: list[dict[str, float]]
    best_condition: str
    worst_condition: str


class AdaptiveMemory:
    def __init__(self, state_manager: StateManager | None = None, db_path: str = 'data/adaptive_memory.db') -> None:
        self.state_manager = state_manager or StateManager()
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = LLMEngine()
        self.current_system_prompt = 'You are PROMETEUSZ autonomous trading intelligence. Prefer evidence-backed, risk-aware JSON outputs.'
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute('CREATE TABLE IF NOT EXISTS decisions (id TEXT PRIMARY KEY, pair TEXT, action TEXT, confidence REAL, quantum_score REAL, timestamp REAL, payload_json TEXT)')
            connection.execute('CREATE TABLE IF NOT EXISTS outcomes (decision_id TEXT, actual_return REAL, measured_at REAL)')
            connection.execute('CREATE TABLE IF NOT EXISTS thresholds (key TEXT PRIMARY KEY, value REAL, updated_at REAL)')
            connection.commit()

    async def record_decision(self, decision: dict[str, Any], outcome: float | None = None) -> None:
        await asyncio.to_thread(self._record_sync, decision, outcome)

    def _record_sync(self, decision: dict[str, Any], outcome: float | None) -> None:
        decision_id = str(decision.get('decision_id') or decision.get('timestamp'))
        with sqlite3.connect(self.db_path) as connection:
            connection.execute('INSERT OR REPLACE INTO decisions(id, pair, action, confidence, quantum_score, timestamp, payload_json) VALUES (?, ?, ?, ?, ?, ?, ?)', (decision_id, decision.get('pair'), decision.get('action'), float(decision.get('confidence', 0.0)), float(decision.get('quantum_score', 0.0)), float(decision.get('timestamp', time.time())), json.dumps(decision)))
            if outcome is not None:
                connection.execute('INSERT INTO outcomes(decision_id, actual_return, measured_at) VALUES (?, ?, ?)', (decision_id, float(outcome), time.time()))
            connection.commit()

    async def decision_history(self, limit: int = 100) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._decision_history_sync, limit)

    def _decision_history_sync(self, limit: int) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute('SELECT payload_json FROM decisions ORDER BY timestamp DESC LIMIT ?', (limit,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    async def outcomes_history(self, limit: int = 100) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._outcomes_history_sync, limit)

    def _outcomes_history_sync(self, limit: int) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute('SELECT decision_id, actual_return, measured_at FROM outcomes ORDER BY measured_at DESC LIMIT ?', (limit,)).fetchall()
        return [{'decision_id': row[0], 'actual_return': row[1], 'measured_at': row[2]} for row in rows]

    async def analyze_accuracy(self) -> AccuracyReport:
        return await asyncio.to_thread(self._analyze_sync)

    def _analyze_sync(self) -> AccuracyReport:
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute('SELECT d.pair, d.action, d.confidence, o.actual_return FROM decisions d JOIN outcomes o ON d.id = o.decision_id').fetchall()
        if not rows:
            return AccuracyReport({}, {}, [], 'insufficient_data', 'insufficient_data')
        pair_stats: dict[str, list[int]] = {}
        action_stats: dict[str, list[int]] = {}
        bins: dict[int, list[int]] = {}
        for pair, action, confidence, outcome in rows:
            success = 1 if (action == 'BUY' and outcome > 0) or (action == 'SELL' and outcome < 0) or (action == 'HOLD' and abs(outcome) < 0.01) or (action == 'HALT' and abs(outcome) < 0.02) else 0
            pair_stats.setdefault(pair, []).append(success)
            action_stats.setdefault(action, []).append(success)
            bucket = min(9, int(float(confidence) * 10))
            bins.setdefault(bucket, []).append(success)
        per_pair = {pair: sum(values) / len(values) for pair, values in pair_stats.items()}
        per_action = {action: sum(values) / len(values) for action, values in action_stats.items()}
        calibration = [{'bucket': bucket / 10, 'accuracy': sum(values) / len(values)} for bucket, values in sorted(bins.items())]
        best = max(per_pair, key=per_pair.get)
        worst = min(per_pair, key=per_pair.get)
        return AccuracyReport(per_pair, per_action, calibration, best, worst)

    async def adapt_thresholds(self) -> dict[str, float]:
        report = await self.analyze_accuracy()
        updates: dict[str, float] = {}
        buy_accuracy = report.per_action_accuracy.get('BUY', 1.0)
        sell_accuracy = report.per_action_accuracy.get('SELL', 1.0)
        if buy_accuracy < 0.55:
            updates['signal_min_confidence'] = 0.65
        if sell_accuracy < 0.55:
            updates['rsi_oversold_threshold'] = 28.0
        for key, value in updates.items():
            await self.state_manager.set(f'threshold:{key}', value)
            await self.state_manager.set('memory:last_threshold_update', updates)
        return updates

    async def generate_insight(self, pair: str) -> str:
        report = await self.analyze_accuracy()
        prompt = f'Analyze decision and outcome correlations for {pair}. Pair accuracy: {report.per_pair_accuracy.get(pair, 0.0):.2f}'
        result = await self.engine.chat([ChatMessage(role='user', content=prompt)])
        return result['message']['content']

    def get_current_system_prompt(self) -> str:
        return self.current_system_prompt

    def set_current_system_prompt(self, value: str) -> None:
        self.current_system_prompt = value
