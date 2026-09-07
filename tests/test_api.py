from fastapi.testclient import TestClient

from backend.main import create_app
from backend.metrics.store import MetricsStore


def test_health_and_metrics_publish_api() -> None:
    store = MetricsStore()
    app = create_app(gpu_enabled=False, metrics_store=store, interval_seconds=10)
    with TestClient(app) as client:
        assert client.get("/api/health").json()["status"] == "ok"
        response = client.post(
            "/api/metrics/inference",
            json={"model_name": "ResearchModel", "throughput": 88, "batch_size": 4},
        )
        assert response.status_code == 200
        current = client.get("/api/metrics").json()
        assert current["inference"]["throughput_tps"] == 88
        assert current["inference"]["model_name"] == "ResearchModel"

