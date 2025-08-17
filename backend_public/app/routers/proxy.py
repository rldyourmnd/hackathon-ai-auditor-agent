from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse, HTMLResponse
import httpx
from ..config import settings

router = APIRouter(prefix="/internal", tags=["internal-proxy"]) 

async def _proxy(request: Request, path: str) -> Response:
    url = f"{settings.internal_api_base.rstrip('/')}/{path}"
    method = request.method

    # Prepare headers (exclude host-specific)
    headers = {k: v for k, v in request.headers.items() if k.lower() not in {"host", "content-length"}}

    # Read body
    body = await request.body()

    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
        resp = await client.request(method, url, params=request.query_params, headers=headers, content=body)

    content_type = resp.headers.get("content-type", "application/octet-stream")
    return Response(content=resp.content, status_code=resp.status_code, headers={"content-type": content_type})

@router.get("/openapi.json")
async def openapi_json():
    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
        r = await client.get(f"{settings.internal_api_base.rstrip('/')}/openapi.json")
        return JSONResponse(status_code=r.status_code, content=r.json())

@router.get("/docs")
async def docs_html():
    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
        r = await client.get(f"{settings.internal_api_base.rstrip('/')}/docs")
        return HTMLResponse(status_code=r.status_code, content=r.text)

@router.api_route("/{path:path}", methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"])
async def proxy_all(path: str, request: Request):
    return await _proxy(request, path)
