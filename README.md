# PROMETEUSZ

PROMETEUSZ is a Python 3.11+ monorepo scaffold for a hybrid AI, quantum, neuromorphic, and trading infrastructure stack.

## Included Phase 1 foundations

- FastAPI gateway with `/health`, `/ai/chat`, `/quantum/optimize`, and Nexus status routes.
- Async AI router with a mockable OpenAI-compatible LLM client, SQLite-backed memory, and Redis state hooks.
- Quantum simulator scaffold with a 4-qubit PennyLane VQE example and portfolio optimization placeholder.
- Bybit public WebSocket market data client with automatic retry/fallback publishing to the event bus.
- Async event bus, module manager, OS bridge, Docker image, and `docker-compose` orchestration.
- Basic pytest coverage for AI, quantum, and Nexus signal flows.

## Project structure

```text
prometeusz/
├── core/
├── nexus/
├── neural_os/
├── interfaces/
├── config/
├── tests/
└── docker/
```

## Quick start

1. Copy `.env.example` to `.env`.
2. Start the stack:
   ```bash
   docker compose -f docker/docker-compose.yml up --build
   ```
3. Open the API docs at `http://localhost:8000/docs`.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest tests/
uvicorn interfaces.api.main:app --reload
```

## Notes

- The AI module defaults to `MOCK_LLM=true` so the scaffold runs without a paid LLM API.
- The quantum layer automatically falls back to a deterministic stub if PennyLane is unavailable.
- The Bybit client uses public market data only and will keep retrying if network connectivity is unavailable.
