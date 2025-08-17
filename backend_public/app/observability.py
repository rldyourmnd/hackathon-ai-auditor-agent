from fastapi import APIRouter, Response
from typing import Dict, Tuple
import threading
import time

# Simple in-process metrics store (thread-safe)
_lock = threading.Lock()
_http_requests_total: Dict[Tuple[str, int], int] = {}
_app_start_time = time.time()

router = APIRouter(tags=["observability"])


def inc_http_request(method: str, status_code: int) -> None:
    key = (method.upper(), int(status_code))
    with _lock:
        _http_requests_total[key] = _http_requests_total.get(key, 0) + 1


def _render_prometheus_text() -> str:
    lines = [
        "# HELP http_requests_total Total HTTP requests processed",
        "# TYPE http_requests_total counter",
    ]
    with _lock:
        for (method, status), value in sorted(_http_requests_total.items()):
            lines.append(
                f'http_requests_total{{method="{method}",status="{status}"}} {value}'
            )
    # Simple uptime gauge
    uptime = max(0.0, time.time() - _app_start_time)
    lines.append("# HELP app_uptime_seconds Uptime of the application in seconds")
    lines.append("# TYPE app_uptime_seconds gauge")
    lines.append(f"app_uptime_seconds {uptime:.0f}")
    return "\n".join(lines) + "\n"


@router.get("/metrics")
def prometheus_metrics() -> Response:
    text = _render_prometheus_text()
    return Response(content=text, media_type="text/plain; version=0.0.4; charset=utf-8")
