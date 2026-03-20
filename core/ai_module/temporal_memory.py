from __future__ import annotations

import io
import json
import math
import sqlite3
import time
import uuid
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class AnalogueMatch:
    pattern_id: str
    similarity: float
    outcome_distribution: dict[str, float]
    context_overlap: float
    timestamp_original: float


class TemporalPatternMemory:
    def __init__(self, db_path: str = 'data/temporal_patterns.db') -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute('CREATE TABLE IF NOT EXISTS patterns (id TEXT PRIMARY KEY, symbol TEXT, features_blob BLOB, outcome_1h REAL, outcome_4h REAL, outcome_24h REAL, context_json TEXT, timestamp REAL)')
            connection.commit()

    def _encode(self, sequence: list[list[float]]) -> bytes:
        return zlib.compress(json.dumps(sequence).encode())

    def _decode(self, blob: bytes) -> list[list[float]]:
        return json.loads(zlib.decompress(blob).decode())

    def store_pattern(self, symbol: str, feature_sequence: list[list[float]], outcome_1h: float, outcome_4h: float, outcome_24h: float, context: dict[str, Any]) -> str:
        pattern_id = str(uuid.uuid4())
        with sqlite3.connect(self.db_path) as connection:
            connection.execute('INSERT INTO patterns(id, symbol, features_blob, outcome_1h, outcome_4h, outcome_24h, context_json, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (pattern_id, symbol, self._encode(feature_sequence), outcome_1h, outcome_4h, outcome_24h, json.dumps(context), time.time()))
            connection.commit()
        return pattern_id

    def dtw(self, s: list[list[float]], t: list[list[float]]) -> float:
        n, m = len(s), len(t)
        dp = [[float('inf')] * (m + 1) for _ in range(n + 1)]
        dp[0][0] = 0.0
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                cost = math.sqrt(sum((s[i - 1][k] - t[j - 1][k]) ** 2 for k in range(min(len(s[i - 1]), len(t[j - 1])))))
                dp[i][j] = cost + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
        return dp[n][m]

    def find_analogues(self, current_sequence: list[list[float]], symbol: str, top_k: int = 5, similarity_threshold: float = 0.85) -> list[AnalogueMatch]:
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute('SELECT id, features_blob, outcome_1h, outcome_4h, outcome_24h, context_json, timestamp FROM patterns WHERE symbol = ?', (symbol,)).fetchall()
        matches: list[AnalogueMatch] = []
        for pattern_id, blob, o1, o4, o24, context_json, ts in rows:
            sequence = self._decode(blob)
            distance = self.dtw(current_sequence, sequence)
            normalized = distance / max(len(current_sequence), 1)
            similarity = max(0.0, 1.0 - normalized)
            if similarity < similarity_threshold:
                continue
            context = json.loads(context_json)
            current_context = {'symbol': symbol}
            overlap = 1.0 if context.get('symbol') == current_context['symbol'] else 0.5
            matches.append(AnalogueMatch(pattern_id, similarity, {'1h': o1, '4h': o4, '24h': o24, 'std': abs(o24 - o1) / 2}, overlap, ts))
        matches.sort(key=lambda item: item.similarity, reverse=True)
        return matches[:top_k]

    def synthesize_forecast(self, analogues: list[AnalogueMatch]) -> dict[str, Any]:
        if not analogues:
            return {'1h_forecast': 0.0, '4h_forecast': 0.0, '24h_forecast': 0.0, 'confidence_interval_95': 0.0, 'n_analogues': 0}
        total_weight = sum(match.similarity for match in analogues) or 1.0
        weighted = lambda key: sum(match.outcome_distribution[key] * match.similarity for match in analogues) / total_weight
        variance = sum((match.outcome_distribution['24h'] - weighted('24h')) ** 2 for match in analogues) / len(analogues)
        return {'1h_forecast': weighted('1h'), '4h_forecast': weighted('4h'), '24h_forecast': weighted('24h'), 'confidence_interval_95': 1.96 * math.sqrt(variance), 'n_analogues': len(analogues)}

    def health(self) -> dict[str, Any]:
        return {'status': 'ok', 'response_time_ms': 0.0}

    def latest_for_symbol(self, symbol: str, limit: int = 5) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute('SELECT id, timestamp FROM patterns WHERE symbol = ? ORDER BY timestamp DESC LIMIT ?', (symbol, limit)).fetchall()
        return [{'pattern_id': row[0], 'timestamp': row[1]} for row in rows]
