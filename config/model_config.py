from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ModelConfig:
    model_name: str = 'yuan3'
    mode: str = 'openai-compatible'


def get_model_config() -> ModelConfig:
    return ModelConfig()
