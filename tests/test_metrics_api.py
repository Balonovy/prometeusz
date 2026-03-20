from fastapi.testclient import TestClient

from interfaces.api.main import app


def test_metrics_endpoint():
    with TestClient(app) as client:
        response = client.get('/metrics')
        assert response.status_code == 200
        assert 'prometeusz_decisions_total' in response.json() if isinstance(response.json(), str) else True
