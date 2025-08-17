import time
import uuid
import json
import logging
from typing import Callable
from fastapi import Request, Response
from ..observability import inc_http_request


async def request_id_middleware(request: Request, call_next: Callable) -> Response:
    """Attach a request id to each request/response for tracing."""
    req_id = request.headers.get("x-request-id") or uuid.uuid4().hex
    request.state.request_id = req_id
    response = await call_next(request)
    response.headers.setdefault("x-request-id", req_id)
    return response


async def logging_middleware(request: Request, call_next: Callable) -> Response:
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    log = {
        "type": "access",
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "duration_ms": duration_ms,
        "request_id": getattr(request.state, "request_id", None),
    }
    logging.getLogger("access").info(json.dumps(log, ensure_ascii=False))
    try:
        inc_http_request(request.method, response.status_code)
    except Exception:
        # Observability should never break request flow
        pass
    return response
