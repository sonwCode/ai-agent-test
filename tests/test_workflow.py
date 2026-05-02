from fastapi.testclient import TestClient

from backend.app.main import app


def test_health():
    with TestClient(app) as client:
        res = client.get("/api/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"


def test_run_task():
    payload = {
        "title": "测试生成运营周报",
        "goal": "基于企业运营制度生成一份周报，包含进展、风险和下周计划。",
        "task_type": "运营周报",
        "context": "需要正式、可复核。",
        "deliverable": "Markdown 周报",
    }
    with TestClient(app) as client:
        res = client.post("/api/tasks/run", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "completed"
        assert data["quality_score"] >= 70
        assert len(data["steps"]) >= 5
        assert data["artifacts"]
