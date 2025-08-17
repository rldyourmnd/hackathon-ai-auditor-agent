import json
import os
from typing import Callable

from fastapi import APIRouter, Request, Response
import httpx
import logging
import time
from urllib.parse import urlparse
import socket

from ..config import settings

router = APIRouter(tags=["spec-proxy"])

logger = logging.getLogger(__name__)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # backend_public
OPENAPI_PATH = os.path.join(ROOT_DIR, "openapi.json")
SWAGGER_HTML_PATH = os.path.join(ROOT_DIR, "Curestry API - Swagger UI.htm")

# Load OpenAPI spec once
with open(OPENAPI_PATH, "r", encoding="utf-8") as f:
    OPENAPI_SPEC = json.load(f)


async def _proxy(request: Request, full_path: str) -> Response:
    # Preserve exact requested path and query
    target_url = f"{settings.internal_api_base.rstrip('/')}/{full_path}"
    parsed = urlparse(target_url)
    upstream_host = parsed.hostname or ""
    try:
        upstream_ip = socket.gethostbyname(upstream_host) if upstream_host else ""
    except Exception:
        upstream_ip = ""
    method = request.method
    headers = {k: v for k, v in request.headers.items() if k.lower() not in {"host", "content-length"}}
    body = await request.body()
    start = time.perf_counter()
    logger.info(
        "proxy_request method=%s path=%s target=%s upstream_host=%s upstream_ip=%s",
        method,
        request.url.path,
        target_url,
        upstream_host,
        upstream_ip,
    )
    try:
        async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
            resp = await client.request(method, target_url, params=request.query_params, headers=headers, content=body)
    except Exception as e:
        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.error(
            "proxy_error method=%s path=%s target=%s err=%s duration_ms=%s upstream_host=%s upstream_ip=%s",
            method,
            request.url.path,
            target_url,
            repr(e),
            duration_ms,
            upstream_host,
            upstream_ip,
        )
        return Response(
            content=b"",
            status_code=502,
            headers={
                "X-Proxy-Upstream": target_url,
                "X-Proxy-Upstream-IP": upstream_ip,
                "X-Proxy-Duration-ms": str(duration_ms),
                "content-type": "application/octet-stream",
            },
        )
    duration_ms = int((time.perf_counter() - start) * 1000)
    logger.info(
        "proxy_response method=%s path=%s status=%s duration_ms=%s upstream_host=%s upstream_ip=%s",
        method,
        request.url.path,
        resp.status_code,
        duration_ms,
        upstream_host,
        upstream_ip,
    )
    # Stream back response
    # Copy upstream headers except hop-by-hop and content-length (Starlette will set it)
    hop_by_hop = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers", "transfer-encoding", "upgrade"}
    out_headers = {k: v for k, v in resp.headers.items() if k.lower() not in hop_by_hop and k.lower() != "content-length"}
    # Ensure content-type present
    out_headers.setdefault("content-type", resp.headers.get("content-type", "application/octet-stream"))
    # Add proxy diagnostic headers
    out_headers["X-Proxy-Upstream"] = target_url
    out_headers["X-Proxy-Upstream-IP"] = upstream_ip
    out_headers["X-Proxy-Duration-ms"] = str(duration_ms)
    return Response(content=resp.content, status_code=resp.status_code, headers=out_headers)


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


# Catch-all proxy for all methods and paths (registered last to avoid shadowing above endpoints)
router.add_api_route(
    path="/{full_path:path}",
    endpoint=_proxy,
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
