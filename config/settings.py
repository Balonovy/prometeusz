from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(slots=True)
class Settings:
    env: str
    host: str
    port: int
    openai_base_url: str
    openai_model: str
    openai_api_key: str
    redis_url: str
    sqlite_path: Path
    bybit_ws_url: str
    bybit_symbols_raw: str
    log_level: str

    @property
    def bybit_symbols(self) -> list[str]:
        return [symbol.strip().upper() for symbol in self.bybit_symbols_raw.split(',') if symbol.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings(
        env=os.getenv('PROMETEUSZ_ENV', 'development'),
        host=os.getenv('PROMETEUSZ_HOST', '0.0.0.0'),
        port=int(os.getenv('PROMETEUSZ_PORT', '8000')),
        openai_base_url=os.getenv('OPENAI_BASE_URL', 'http://localhost:11434/v1'),
        openai_model=os.getenv('OPENAI_MODEL', 'prometeusz-local'),
        openai_api_key=os.getenv('OPENAI_API_KEY', ''),
        redis_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        sqlite_path=Path(os.getenv('SQLITE_PATH', 'data/prometeusz.db')),
        bybit_ws_url=os.getenv('BYBIT_WS_URL', 'wss://stream.bybit.com/v5/public/linear'),
        bybit_symbols_raw=os.getenv('BYBIT_SYMBOLS', 'JASMYUSDT,DOGEUSDT,SEIUSDT'),
        log_level=os.getenv('LOG_LEVEL', 'INFO'),
    )
    settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    return settings
