import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.anyio
async def test_openapi_contains_analysis_endpoints_and_schemas():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        r = await client.get("/public-openapi.json")
        assert r.status_code == 200
        spec = r.json()
        paths = spec.get("paths", {})

        # Endpoints present
        assert "/api/analyze" in paths
        assert "/api/analyze/clarify" in paths
        assert "/api/analyze/apply" in paths
        assert "/api/analyses/{analysis_id}" in paths
        assert "/api/export" in paths

        # Response schemas exist
        components = spec.get("components", {}).get("schemas", {})
        assert "AnalyzeResponse" in components
        assert "ClarifyResponse" in components
        assert "ApplyResponse" in components
        assert "ExportResponse" in components

        # DTO fields sanity
        analyze_props = components["AnalyzeResponse"]["properties"]
        assert "analysis_id" in analyze_props
        assert "report" in analyze_props
        assert "patches" in analyze_props
        assert "questions" in analyze_props
