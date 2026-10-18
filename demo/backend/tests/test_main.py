import httpx
from fastapi.testclient import TestClient

from app import providers
from app.main import create_app


def test_health_and_demo_data_are_explicitly_labeled(tmp_path):
    app = create_app(tmp_path / "test.sqlite3")
    with TestClient(app) as client:
        health = client.get("/health")
        overview = client.get("/api/demo/overview")

    assert health.status_code == 200
    assert health.json() == {"status": "ok", "mode": "demo"}
    assert overview.status_code == 200
    payload = overview.json()
    assert payload["data_mode"] == "frozen-demo-snapshot"
    assert payload["snapshot_at"] == "2026-10-16T15:00:00+08:00"
    assert "固定于 2026-10-16 15:00" in payload["notice"]
    assert len(payload["funds"]) == 3
    assert len(payload["stocks"]) == 3
    assert len(payload["headlines"]) == 2


def test_market_snapshot_does_not_change_between_requests(tmp_path):
    app = create_app(tmp_path / "test.sqlite3")
    with TestClient(app) as client:
        first = client.get("/api/demo/overview").json()
        second = client.get("/api/demo/overview").json()

    assert first == second
    assert all(item["published_at"].startswith("2026-10-16T") for item in first["headlines"])


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


def test_market_endpoints_explain_when_provider_is_not_configured(tmp_path, monkeypatch):
    monkeypatch.delenv("FUND_MARKET_API_URL", raising=False)
    monkeypatch.delenv("STOCK_MARKET_API_URL", raising=False)
    app = create_app(tmp_path / "test.sqlite3")

    with TestClient(app) as client:
        funds = client.get("/api/market/funds")
        stocks = client.get("/api/market/stocks")

    assert funds.status_code == 503
    assert "基金" in funds.json()["detail"]
    assert stocks.status_code == 503
    assert "股票" in stocks.json()["detail"]


def test_market_endpoint_uses_configured_url_and_server_side_auth(tmp_path, monkeypatch):
    monkeypatch.setenv("FUND_MARKET_API_URL", "https://provider.example/v1/funds")
    monkeypatch.setenv("FUND_MARKET_API_KEY", "test-key")
    monkeypatch.setenv("FUND_MARKET_API_KEY_HEADER", "X-Api-Key")
    monkeypatch.setenv("FUND_MARKET_API_AUTH_SCHEME", "")

    def handle_request(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://provider.example/v1/funds"
        assert request.headers["X-Api-Key"] == "test-key"
        return httpx.Response(200, json={"items": [{"code": "000001", "name": "示例基金"}]})

    transport = httpx.MockTransport(handle_request)
    monkeypatch.setattr(
        providers,
        "create_http_client",
        lambda: httpx.AsyncClient(transport=transport, timeout=1),
    )
    app = create_app(tmp_path / "test.sqlite3")

    with TestClient(app) as client:
        response = client.get("/api/market/funds")

    assert response.status_code == 200
    assert response.json() == {"items": [{"code": "000001", "name": "示例基金"}]}
