from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

DEFAULT_SYMBOLS = [
    'SOLUSDT', 'AVAXUSDT', 'DOGEUSDT', 'MATICUSDT', 'LINKUSDT', 'DOTUSDT', 'ADAUSDT', 'XRPUSDT',
    'LTCUSDT', 'ATOMUSDT', 'NEARUSDT', 'APTUSDT', 'ARBUSDT', 'OPUSDT', 'INJUSDT', 'SUIUSDT',
    'SEIUSDT', 'TIAUSDT', 'JASMYUSDT', 'WIFUSDT',
]


def _parse_symbols(raw: str | None) -> list[str]:
    if not raw:
        return list(DEFAULT_SYMBOLS)
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list) and parsed:
            return [str(item).strip().upper() for item in parsed if str(item).strip()]
    except json.JSONDecodeError:
        pass
    values = [part.strip().upper() for part in raw.split(',') if part.strip()]
    return values or list(DEFAULT_SYMBOLS)


@dataclass(slots=True)
class Settings:
    openai_base_url: str = 'http://127.0.0.1:11434/v1'
    openai_api_key: str = ''
    llm_model_name: str = 'yuan3'
    mock_llm: bool = True
    redis_url: str = 'redis://redis:6379/0'
    sqlite_path: str = 'data/prometeusz.db'
    bybit_ws_url: str = 'wss://stream.bybit.com/v5/public/linear'
    bybit_symbols: list[str] = field(default_factory=lambda: list(DEFAULT_SYMBOLS))
    websocket_retry_seconds: int = 5
    http_timeout_seconds: float = 10.0
    market_history_limit: int = 240
    signal_min_confidence: float = 0.6
    agent_interval_seconds: float = 5.0
    watchdog_interval_seconds: float = 10.0
    portfolio_rebalance_seconds: float = 60.0
    quantum_iterations: int = 200
    mock_market_seed: int = 7

    def ensure_data_dir(self) -> Path:
        path = Path(self.sqlite_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path.parent


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings(
        openai_base_url=os.getenv('OPENAI_BASE_URL', 'http://127.0.0.1:11434/v1'),
        openai_api_key=os.getenv('OPENAI_API_KEY', ''),
        llm_model_name=os.getenv('LLM_MODEL_NAME', 'yuan3'),
        mock_llm=os.getenv('MOCK_LLM', 'true').lower() in {'1', 'true', 'yes', 'on'},
        redis_url=os.getenv('REDIS_URL', 'redis://redis:6379/0'),
        sqlite_path=os.getenv('SQLITE_PATH', 'data/prometeusz.db'),
        bybit_ws_url=os.getenv('BYBIT_WS_URL', 'wss://stream.bybit.com/v5/public/linear'),
        bybit_symbols=_parse_symbols(os.getenv('BYBIT_SYMBOLS')),
        websocket_retry_seconds=int(os.getenv('WEBSOCKET_RETRY_SECONDS', '5')),
        http_timeout_seconds=float(os.getenv('HTTP_TIMEOUT_SECONDS', '10')),
        market_history_limit=int(os.getenv('MARKET_HISTORY_LIMIT', '240')),
        signal_min_confidence=float(os.getenv('SIGNAL_MIN_CONFIDENCE', '0.6')),
        agent_interval_seconds=float(os.getenv('AGENT_INTERVAL_SECONDS', '5')),
        watchdog_interval_seconds=float(os.getenv('WATCHDOG_INTERVAL_SECONDS', '10')),
        portfolio_rebalance_seconds=float(os.getenv('PORTFOLIO_REBALANCE_SECONDS', '60')),
        quantum_iterations=int(os.getenv('QUANTUM_ITERATIONS', '200')),
        mock_market_seed=int(os.getenv('MOCK_MARKET_SEED', '7')),
    )
    settings.ensure_data_dir()
    return settings
