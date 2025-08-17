import pytest
import anyio
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.anyio
async def test_healthz_ok():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        r = await client.get("/healthz")
        assert r.status_code == 200
        body = r.json()
        assert body.get("status") == "ok"


@pytest.mark.anyio
async def test_metrics_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        # Trigger a request so counters increment
        _ = await client.get("/")
        r = await client.get("/metrics")
        assert r.status_code == 200
        text = r.text
        assert "http_requests_total" in text
        assert "app_uptime_seconds" in text
