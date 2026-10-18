from fastapi.testclient import TestClient

from app.main import create_app


def test_health_and_demo_data_are_explicitly_labeled(tmp_path):
    app = create_app(tmp_path / "test.sqlite3")
    with TestClient(app) as client:
        health = client.get("/health")
        overview = client.get("/api/demo/overview")

    assert health.status_code == 200
    assert health.json() == {"status": "ok", "mode": "demo"}
    assert overview.status_code == 200
    assert overview.json()["data_mode"] == "fictional-demo"
    assert "虚构示例" in overview.json()["notice"]


def test_watchlist_can_be_created_listed_and_removed(tmp_path):
    app = create_app(tmp_path / "test.sqlite3")
    with TestClient(app) as client:
        created = client.post(
            "/api/demo/watchlist",
            json={"code": "demo01", "name": "示例基金"},
        )
        listed = client.get("/api/demo/watchlist")
        removed = client.delete(f"/api/demo/watchlist/{created.json()['id']}")
        listed_after_remove = client.get("/api/demo/watchlist")

    assert created.status_code == 201
    assert created.json()["code"] == "DEMO01"
    assert listed.json()[0]["name"] == "示例基金"
    assert removed.status_code == 204
    assert listed_after_remove.json() == []


def test_watchlist_rejects_duplicates_and_invalid_codes(tmp_path):
    app = create_app(tmp_path / "test.sqlite3")
    with TestClient(app) as client:
        first = client.post(
            "/api/demo/watchlist",
            json={"code": "DEMO01", "name": "示例基金"},
        )
        duplicate = client.post(
            "/api/demo/watchlist",
            json={"code": "DEMO01", "name": "另一个名字"},
        )
        invalid = client.post(
            "/api/demo/watchlist",
            json={"code": "A/../B", "name": "无效代码"},
        )

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert invalid.status_code == 422
