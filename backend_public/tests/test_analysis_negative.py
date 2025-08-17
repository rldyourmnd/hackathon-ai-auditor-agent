import uuid
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.infra.pipeline_client import PipelineClient, PipelineTimeoutError, PipelineHTTPError, PipelineError


class _ErrorPipeline(PipelineClient):
    def __init__(self, mode: str):
        # avoid super init (no httpx client)
        self.base_url = "http://mock"
        self._mode = mode

    async def analyze(self, prompt: str, format_type: str = "auto", language: str = "auto"):
        if self._mode == "timeout":
            raise PipelineTimeoutError("timeout")
        if self._mode == "http400":
            raise PipelineHTTPError(status_code=400, message="bad request")
        if self._mode == "http429":
            raise PipelineHTTPError(status_code=429, message="too many requests")
        if self._mode == "error":
            raise PipelineError("generic pipeline error")
        return {}

    async def clarify(self, analysis_id: str, answers):
        # not used in negative analyze tests
        raise NotImplementedError()

    async def apply_patches(self, analysis_id: str, patch_ids):
        # not used in negative analyze tests
        raise NotImplementedError()


async def _override_pipeline_factory(instance: PipelineClient):
    async def _factory():
        return instance
    return _factory


@pytest.mark.anyio
@pytest.mark.parametrize(
    "mode,expected_status",
    [
        ("timeout", 504),
        ("http400", 400),
        ("http429", 429),
        ("error", 502),
    ],
)
async def test_analyze_pipeline_errors(mode, expected_status):
    from app.infra.pipeline_client import get_pipeline_client

    pipeline = _ErrorPipeline(mode)
    app.dependency_overrides[get_pipeline_client] = await _override_pipeline_factory(pipeline)

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            payload = {"prompt": {"content": "x", "format_type": "plain", "language": "en"}}
            r = await client.post("/api/analyze", json=payload)
            assert r.status_code == expected_status, r.text
    finally:
        app.dependency_overrides.pop(get_pipeline_client, None)


@pytest.mark.anyio
async def test_get_analysis_not_found():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        random_id = str(uuid.uuid4())
        r = await client.get(f"/api/analyses/{random_id}")
        assert r.status_code == 404


@pytest.mark.anyio
async def test_export_not_found():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        random_id = str(uuid.uuid4())
        r = await client.get("/api/export", params={"analysis_id": random_id})
        assert r.status_code == 404


@pytest.mark.anyio
async def test_clarify_not_found():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        random_id = str(uuid.uuid4())
        payload = {"analysis_id": random_id, "answers": [{"question_id": "q1", "answer": "a"}]}
        r = await client.post("/api/analyze/clarify", json=payload)
        assert r.status_code == 404


@pytest.mark.anyio
async def test_apply_not_found():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        random_id = str(uuid.uuid4())
        payload = {"analysis_id": random_id, "patch_ids": ["p1"]}
        r = await client.post("/api/analyze/apply", json=payload)
        assert r.status_code == 404
