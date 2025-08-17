import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.infra.pipeline_client import PipelineClient


class _MockPipeline(PipelineClient):
    def __init__(self):
        # Do not call super to avoid creating httpx client
        self.base_url = "http://mock"

    async def analyze(self, prompt: str, format_type: str = "auto", language: str = "auto"):
        return {
            "version": "test-1",
            "metadata": {"model": "gpt-test"},
            "report": {
                "overall_score": 7.0,
                "judge_score": {"score": 7.0, "rationale": "ok", "criteria_scores": {}, "confidence": 0.8},
                "semantic_entropy": {"entropy": 0.2, "spread": 0.1, "clusters": 2, "samples": []},
                "complexity_score": 5.0,
                "length_words": 10,
                "length_chars": 50,
                "risk_level": "medium",
                "contradictions": [],
                "format_valid": True,
                "detected_language": "en",
                "translated": False,
            },
            "patches": [],
            "questions": [],
        }

    async def clarify(self, analysis_id: str, answers):
        return {
            "report": {
                "overall_score": 7.5,
                "judge_score": {"score": 7.5, "rationale": "better", "criteria_scores": {}, "confidence": 0.8},
                "semantic_entropy": {"entropy": 0.18, "spread": 0.1, "clusters": 2, "samples": []},
                "complexity_score": 5.0,
                "length_words": 10,
                "length_chars": 50,
                "risk_level": "medium",
                "contradictions": [],
                "format_valid": True,
            },
            "new_patches": [],
            "detected_language": "en",
            "translated": False,
        }

    async def apply_patches(self, analysis_id: str, patch_ids):
        return {
            "improved_prompt": "improved",
            "applied_patches": patch_ids,
            "failed_patches": [],
            "improvement_summary": "ok",
            "quality_gain": 0.5,
        }


@pytest.fixture(autouse=True)
def override_pipeline(dep_override_cache={}):
    from app.infra.pipeline_client import get_pipeline_client

    async def _factory():
        return _MockPipeline()

    app.dependency_overrides[get_pipeline_client] = _factory
    yield
    app.dependency_overrides.pop(get_pipeline_client, None)


@pytest.mark.anyio
async def test_analyze_and_get_and_export_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        # analyze
        payload = {"prompt": {"content": "hello", "format_type": "plain", "language": "en"}}
        r = await client.post("/api/analyze", json=payload)
        assert r.status_code == 200, r.text
        body = r.json()
        analysis_id = body["analysis_id"]

        # get analysis
        r2 = await client.get(f"/api/analyses/{analysis_id}")
        assert r2.status_code == 200

        # export
        r3 = await client.get("/api/export", params={"analysis_id": analysis_id})
        assert r3.status_code == 200
        exp = r3.json()
        assert exp["analysis_id"] == analysis_id
        assert "report" in exp


@pytest.mark.anyio
async def test_clarify_and_apply():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        # First analyze to create an analysis
        payload = {"prompt": {"content": "hello", "format_type": "plain", "language": "en"}}
        r = await client.post("/api/analyze", json=payload)
        assert r.status_code == 200
        analysis_id = r.json()["analysis_id"]

        # clarify
        clr = {"analysis_id": analysis_id, "answers": [{"question_id": "q1", "answer": "a"}]}
        r2 = await client.post("/api/analyze/clarify", json=clr)
        assert r2.status_code == 200
        body2 = r2.json()
        assert body2["analysis_id"] == analysis_id
        assert "updated_report" in body2

        # apply
        app_req = {"analysis_id": analysis_id, "patch_ids": ["p1", "p2"]}
        r3 = await client.post("/api/analyze/apply", json=app_req)
        assert r3.status_code == 200
        body3 = r3.json()
        assert body3["analysis_id"] == analysis_id
        assert body3["applied_patches"] == ["p1", "p2"]
