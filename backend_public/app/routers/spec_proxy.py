import json
import os
from typing import Callable

from fastapi import APIRouter, Request, Response
import httpx

from ..config import settings

router = APIRouter(tags=["spec-proxy"])

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend_public
OPENAPI_PATH = os.path.join(ROOT_DIR, "openapi.json")
SWAGGER_HTML_PATH = os.path.join(ROOT_DIR, "Curestry API - Swagger UI.htm")

# Load OpenAPI spec once
with open(OPENAPI_PATH, "r", encoding="utf-8") as f:
    OPENAPI_SPEC = json.load(f)


def make_proxy_handler(_: str) -> Callable:
    async def handler(request: Request, **kwargs) -> Response:
        # Preserve the exact requested path (with rendered params and dots)
        target_path = request.url.path
        url = f"{settings.internal_api_base.rstrip('/')}{target_path}"
        method = request.method
        headers = {k: v for k, v in request.headers.items() if k.lower() not in {"host", "content-length"}}
        body = await request.body()
        async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
            resp = await client.request(method, url, params=request.query_params, headers=headers, content=body)
        content_type = resp.headers.get("content-type", "application/octet-stream")
        return Response(content=resp.content, status_code=resp.status_code, headers={"content-type": content_type})

    return handler


# Register routes from the OpenAPI spec
for raw_path, ops in OPENAPI_SPEC.get("paths", {}).items():
    # Ensure FastAPI-style path parameters {id} -> {id}
    fastapi_path = raw_path  # already compatible
    methods = [m.upper() for m in ops.keys()]
    router.add_api_route(
        path=fastapi_path,
        endpoint=make_proxy_handler(raw_path),
        methods=methods,
    )


@router.get("/openapi.json")
async def serve_openapi():
    return OPENAPI_SPEC


@router.get("/docs")
async def serve_swagger_html():
    # Return saved Swagger HTML as-is
    if os.path.exists(SWAGGER_HTML_PATH):
        with open(SWAGGER_HTML_PATH, "r", encoding="utf-8") as f:
            html = f.read()
        # Optionally could rewrite spec URL, but assuming it points to /openapi.json
        return Response(content=html, media_type="text/html")
    return Response(content="<h1>Swagger UI not available</h1>", media_type="text/html", status_code=404)
