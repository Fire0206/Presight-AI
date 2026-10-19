import json

import httpx
from fastapi.testclient import TestClient

from app import providers
from app import model_api
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
    assert removed.content == b""
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


def test_model_status_is_false_by_default_and_does_not_expose_secrets(tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_API_KEY", "never-return-this")
    monkeypatch.setenv("MODEL_API_URL", "https://provider.example/v1/chat/completions")
    monkeypatch.setenv("MODEL_NAME", "private-model-id")
    monkeypatch.setenv("MODEL_CHAT_ENABLED", "false")
    app = create_app(tmp_path / "test.sqlite3")

    with TestClient(app) as client:
        response = client.get("/api/demo/model-status")

    assert response.status_code == 200
    assert response.json() == {"configured": False}
    assert "never-return-this" not in response.text
    assert "private-model-id" not in response.text


def test_model_status_handles_malformed_endpoint_without_exposing_configuration(tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_CHAT_ENABLED", "true")
    monkeypatch.setenv("MODEL_API_URL", "https://[")
    monkeypatch.setenv("MODEL_API_KEY", "server-only-key")
    monkeypatch.setenv("MODEL_NAME", "private-model-id")
    app = create_app(tmp_path / "test.sqlite3")

    with TestClient(app) as client:
        response = client.get("/api/demo/model-status")

    assert response.status_code == 200
    assert response.json() == {"configured": False}
    assert "server-only-key" not in response.text
    assert "private-model-id" not in response.text


def test_model_chat_uses_backend_secret_and_returns_only_answer(tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_CHAT_ENABLED", "true")
    monkeypatch.setenv("MODEL_API_URL", "https://provider.example/v1/chat/completions")
    monkeypatch.setenv("MODEL_API_KEY", "server-only-test-key")
    monkeypatch.setenv("MODEL_NAME", "demo-model")
    monkeypatch.setenv("MODEL_MAX_TOKENS", "999999")

    def handle_request(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://provider.example/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer server-only-test-key"
        payload = json.loads(request.content)
        assert payload["model"] == "demo-model"
        assert payload["max_tokens"] == model_api.MAX_COMPLETION_TOKENS
        assert payload["stream"] is False
        return httpx.Response(200, json={
            "choices": [{"message": {"content": "## 结论\n\n回答", "reasoning_content": "不应泄露"}}],
        })

    transport = httpx.MockTransport(handle_request)
    monkeypatch.setattr(
        model_api,
        "create_http_client",
        lambda timeout_seconds: httpx.AsyncClient(transport=transport, timeout=1),
    )
    app = create_app(tmp_path / "test.sqlite3")

    with TestClient(app) as client:
        response = client.post("/api/demo/chat", json={"messages": [{"role": "user", "content": "你好"}]})

    assert response.status_code == 200
    assert response.json() == {"answer": "## 结论\n\n回答"}
    assert "不应泄露" not in response.text
    assert "server-only-test-key" not in response.text


def test_model_chat_is_disabled_unless_configured_and_bounds_input(tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_CHAT_ENABLED", "false")
    app = create_app(tmp_path / "test.sqlite3")

    with TestClient(app) as client:
        disabled = client.post("/api/demo/chat", json={"messages": [{"role": "user", "content": "hello"}]})
        too_long = client.post("/api/demo/chat", json={"messages": [{"role": "user", "content": "x" * 8_001}]})
        too_many = client.post("/api/demo/chat", json={"messages": [{"role": "user", "content": str(index)} for index in range(13)]})
        total_too_long = client.post("/api/demo/chat", json={"messages": [
            {"role": "user", "content": "x" * 8_000},
            {"role": "assistant", "content": "y" * 8_000},
            {"role": "user", "content": "z" * 1},
        ]})

    assert disabled.status_code == 503
    assert too_long.status_code == 422
    assert too_many.status_code == 422
    assert total_too_long.status_code == 413
