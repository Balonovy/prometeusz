# Project PROMETEUSZ

Project PROMETEUSZ is a modular monorepo scaffold for a quantum-neuromorphic-AI hybrid infrastructure stack. Phase 1 focuses on a working FastAPI gateway, a PennyLane-based quantum simulator, a Bybit market data connector, and an async AI routing module with persistence.

## Repository Layout

- `core/ai_module`: Async AI service with routing, safety checks, and SQLite-backed memory.
- `core/quantum_layer`: PennyLane simulator, VQE/QAOA-inspired optimizer, and cloud bridge scaffolding.
- `core/neuromorphic`: Event-driven and spiking-neural primitives for future modules.
- `nexus`: Trading market data ingestion, signal generation, and dashboard aggregation.
- `neural_os`: Event bus, module manager, state manager, and OS bridge for system integration.
- `interfaces/api`: FastAPI gateway and service routers.
- `interfaces/websocket`: Live feed websocket endpoint.
- `config`: Environment-driven runtime configuration.
- `tests`: Pytest coverage for AI, quantum, and Nexus subsystems.
- `docker`: Container build and compose orchestration.

## Quick Start

1. Copy `.env.example` to `.env` and adjust settings as needed.
2. Install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Run the API locally:
   ```bash
   uvicorn interfaces.api.main:app --reload
   ```
4. Or run the full Phase 1 stack:
   ```bash
   docker compose -f docker/docker-compose.yml up --build
   ```

## Key Endpoints

- `GET /health`: gateway health and module inventory.
- `POST /ai/chat`: AI router endpoint compatible with OpenAI-style backends.
- `POST /quantum/optimize`: runs a 4-qubit variational circuit and portfolio optimizer.
- `GET /nexus/market`: latest Bybit/fallback market snapshots.
- `GET /nexus/signals`: signal engine output with quantum enhancement and veto status.
- `WS /ws/live`: live market and signal stream.

## Test Suite

```bash
pytest tests/
```

## Notes

- The Bybit connector attempts a live public WebSocket connection and automatically falls back to deterministic mock data if the network is unavailable.
- The AI engine first tries an OpenAI-compatible backend and falls back to a local scaffold response when no backend is configured.
- Redis is optional for local development; the state manager falls back to in-memory storage when Redis is unavailable.
