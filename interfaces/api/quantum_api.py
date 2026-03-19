from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from core.quantum_layer.cloud_bridge import CloudBridge
from core.quantum_layer.finance_qml import QuantumFinanceModel
from core.quantum_layer.simulator import QuantumSimulator


router = APIRouter(prefix='/quantum', tags=['quantum'])
simulator = QuantumSimulator()
finance_model = QuantumFinanceModel()
cloud_bridge = CloudBridge()


class OptimizeRequest(BaseModel):
    steps: int = Field(default=15, ge=1, le=100)


@router.get('/health')
async def quantum_health() -> dict[str, str]:
    return {'status': 'ok', 'service': 'quantum'}


@router.post('/optimize')
async def optimize(request: OptimizeRequest) -> dict[str, object]:
    vqe = simulator.run_vqe(steps=request.steps)
    portfolio = finance_model.optimize_demo_portfolio()
    return {
        'vqe': vqe.__dict__,
        'portfolio': portfolio.__dict__,
        'cloud': cloud_bridge.status(),
    }
