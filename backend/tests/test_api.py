import asyncio

from fastapi.testclient import TestClient

from app.core.db import init_db
from app.main import app
from app.services.tasks import task_manager

client = TestClient(app)


def setup_module():
    init_db()


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_settings_roundtrip():
    payload = {
        "llm": {
            "baseUrl": "https://example.com/v1",
            "apiKey": "sk-test",
            "model": "demo",
            "temperature": 0.5,
        },
        "collect": {
            "defaultCount": 40,
            "rateLevel": "standard",
            "concurrency": 2,
            "includeComments": True,
        },
    }
    r = client.put("/api/settings", json=payload)
    assert r.status_code == 200
    r2 = client.get("/api/settings")
    assert r2.json()["llm"]["model"] == "demo"
    assert r2.json()["collect"]["defaultCount"] == 40


def test_create_task_and_collect_flow():
    r = client.post("/api/collect/tasks", json={"topic": "测试主题", "total": 5})
    assert r.status_code == 200
    task_id = r.json()["id"]
    assert r.json()["status"] in ("pending", "running")

    # TestClient 的每请求事件循环会回收后台任务，这里直接驱动采集协程完成。
    asyncio.run(task_manager.run_task(task_id))
    t = client.get(f"/api/collect/tasks/{task_id}").json()
    assert t["status"] == "success"

    notes = client.get(f"/api/notes?taskId={task_id}").json()
    assert len(notes) == 5

    analysis = client.get(f"/api/analysis/{task_id}").json()
    assert "keywords" in analysis and "ranking" in analysis

    bd = client.post("/api/analysis/breakdown", json={"noteId": notes[0]["id"]})
    assert bd.status_code == 200
    assert bd.json()["noteId"] == notes[0]["id"]


def test_compose_heuristic():
    # 清空 LLM 设置，确保走启发式兜底（不依赖 test_settings_roundtrip 留下的状态）
    client.put(
        "/api/settings",
        json={
            "llm": {"baseUrl": "", "apiKey": "", "model": "", "temperature": 0.5},
            "collect": {
                "defaultCount": 40,
                "rateLevel": "standard",
                "concurrency": 2,
                "includeComments": True,
            },
        },
    )
    r = client.post("/api/compose", json={"topic": "平价护肤"})
    assert r.status_code == 200
    data = r.json()
    assert len(data["titles"]) >= 1
    assert "平价护肤" in data["body"]
    assert len(data["hashtags"]) >= 1
    assert len(data["imageSuggestions"]) >= 1
