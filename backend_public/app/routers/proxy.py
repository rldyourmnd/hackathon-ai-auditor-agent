from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse, HTMLResponse
import httpx
import time
from typing import Any, Tuple
from ..config import settings

router = APIRouter(prefix="/internal", tags=["internal-proxy"]) 

# Simple in-memory TTL cache (since Redis is optional)
_CACHE: dict[str, Tuple[float, Any]] = {}

def _cache_get(key: str):
    now = time.time()
    data = _CACHE.get(key)
    if not data:
        return None
    exp, value = data
    if exp < now:
        _CACHE.pop(key, None)
        return None
    return value

def _cache_set(key: str, value: Any, ttl_seconds: int = 60):
    _CACHE[key] = (time.time() + ttl_seconds, value)

async def _proxy(request: Request, path: str) -> Response:
    url = f"{settings.internal_api_base.rstrip('/')}/{path}"
    method = request.method

    # Prepare headers (exclude host-specific)
    headers = {k: v for k, v in request.headers.items() if k.lower() not in {"host", "content-length"}}

    # Read body
    body = await request.body()

    try:
        async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
            resp = await client.request(method, url, params=request.query_params, headers=headers, content=body)
    except httpx.ReadTimeout:
        return JSONResponse(status_code=504, content={"message": "Upstream timeout", "path": path})
    except httpx.ConnectTimeout:
        return JSONResponse(status_code=504, content={"message": "Upstream connect timeout", "path": path})
    except httpx.RequestError as e:
        return JSONResponse(status_code=502, content={"message": "Upstream request error", "detail": str(e), "path": path})

    content_type = resp.headers.get("content-type", "application/octet-stream")
    return Response(content=resp.content, status_code=resp.status_code, headers={"content-type": content_type})

@router.get("/openapi.json")
async def openapi_json():
    ck = "openapi.json"
    cached = _cache_get(ck)
    if cached is not None:
        status_code, content = cached
        return JSONResponse(status_code=status_code, content=content)
    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
        r = await client.get(f"{settings.internal_api_base.rstrip('/')}/openapi.json")
        content = r.json()
        _cache_set(ck, (r.status_code, content), ttl_seconds=60)
        return JSONResponse(status_code=r.status_code, content=content)

@router.get("/docs")
async def docs_html():
    ck = "docs.html"
    cached = _cache_get(ck)
    if cached is not None:
        status_code, content = cached
        return HTMLResponse(status_code=status_code, content=content)
    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
        r = await client.get(f"{settings.internal_api_base.rstrip('/')}/docs")
        content = r.text
        _cache_set(ck, (r.status_code, content), ttl_seconds=60)
        return HTMLResponse(status_code=r.status_code, content=content)

@router.api_route("/{path:path}", methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"])
async def proxy_all(path: str, request: Request):
    return await _proxy(request, path)
