import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.api import routes


class MockRunner:
    def run(self, prompt: str):
        return {
            "prompt": prompt,
            "intent": {"intent": "build"},
            "plan": {"steps": []},
            "architecture": {"files": []},
            "project": {"main.py": "print('ok')"},
            "files": {"main.py": "print('ok')"},
            "manifest": {"entrypoint": "main.py", "files": ["main.py"]},
            "code": "print('ok')",
            "review": {"issues": []},
            "attempts": [{"attempt": 1, "issues_count": {"total": 0}}],
            "retries_used": 0,
            "execution": {"success": True, "exit_code": 0, "output": "ok"},
            "metrics": {
                "run_id": "test-mock-run",
                "prompt": prompt,
                "total_latency_ms": 12.5,
                "execution_success": True,
                "files_generated": 1,
            },
        }


@pytest.fixture(autouse=True)
def setup_mock_runner():
    routes.set_runner(MockRunner())


def test_health_endpoints():
    client = TestClient(app)
    r1 = client.get("/health")
    assert r1.status_code == 200
    assert r1.json() == {"status": "ok"}

    r2 = client.get("/api/health")
    assert r2.status_code == 200
    assert r2.json() == {"status": "ok"}


def test_api_runs_and_metrics():
    client = TestClient(app)

    # 1. Post a run
    post_res = client.post("/api/run", json={"prompt": "Build a test app"})
    assert post_res.status_code == 200
    data = post_res.json()
    assert "run_id" in data
    run_id = data["run_id"]

    # 2. List runs
    list_res = client.get("/api/runs")
    assert list_res.status_code == 200
    runs = list_res.json().get("runs", [])
    assert any(r["id"] == run_id for r in runs)

    # 3. Get specific run
    get_res = client.get(f"/api/runs/{run_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == run_id

    # 4. Get 404 for invalid run
    not_found = client.get("/api/runs/non-existent-uuid")
    assert not_found.status_code == 404

    # 5. Get metrics
    metrics_res = client.get("/api/metrics")
    assert metrics_res.status_code == 200
    assert "aggregates" in metrics_res.json()
