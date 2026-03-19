from dataclasses import dataclass


@dataclass(slots=True)
class ModelConfig:
    provider: str = 'openai-compatible'
    model_name: str = 'prometeusz-local'
    temperature: float = 0.2
    max_tokens: int = 256


DEFAULT_MODEL_CONFIG = ModelConfig()
