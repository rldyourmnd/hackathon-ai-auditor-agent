import logging
import uuid
from datetime import datetime

from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ..dto.common import ErrorResponse
from ..infra.pipeline_client import PipelineError, PipelineTimeoutError, PipelineHTTPError

logger = logging.getLogger(__name__)


async def error_handling_middleware(request: Request, call_next):
    """Global error handling middleware with pipeline error normalization."""

    request_id = getattr(request.state, "request_id", None) or str(uuid.uuid4())
    request.state.request_id = request_id

    try:
        response = await call_next(request)
        return response

    except PipelineTimeoutError as e:
        logger.error("Pipeline timeout [%s]: %s", request_id, e)
        return JSONResponse(
            status_code=504,
            content=ErrorResponse(
                message="Analysis service is taking longer than expected. Please try again in a few minutes.",
                error_code="PIPELINE_TIMEOUT",
                timestamp=datetime.utcnow(),
                path=str(request.url.path),
                request_id=request_id,
                details={"retry_after": "2-3 minutes", "support_message": "If this persists, contact support with request ID"},
            ).model_dump(),
        )

    except PipelineHTTPError as e:
        logger.error("Pipeline HTTP error [%s]: %s", request_id, e)
        if e.status_code == 400:
            status_code = 400
            message = "Invalid prompt format or content. Please check your input."
            error_code = "INVALID_PROMPT"
        elif e.status_code == 429:
            status_code = 429
            message = "Analysis service is busy. Please try again in a moment."
            error_code = "RATE_LIMITED"
        else:
            status_code = 502
            message = "Analysis service error. Please try again."
            error_code = "PIPELINE_ERROR"

        return JSONResponse(
            status_code=status_code,
            content=ErrorResponse(
                message=message,
                error_code=error_code,
                timestamp=datetime.utcnow(),
                path=str(request.url.path),
                request_id=request_id,
            ).model_dump(),
        )

    except PipelineError as e:
        logger.error("Pipeline error [%s]: %s", request_id, e)
        return JSONResponse(
            status_code=502,
            content=ErrorResponse(
                message="Analysis service temporarily unavailable. Please try again.",
                error_code="PIPELINE_UNAVAILABLE",
                timestamp=datetime.utcnow(),
                path=str(request.url.path),
                request_id=request_id,
                details={"retry_after": "1-2 minutes"},
            ).model_dump(),
        )

    except HTTPException as e:
        logger.warning("HTTP exception [%s]: %s", request_id, e.detail)
        return JSONResponse(
            status_code=e.status_code,
            content=ErrorResponse(
                message=e.detail,
                error_code="HTTP_ERROR",
                timestamp=datetime.utcnow(),
                path=str(request.url.path),
                request_id=request_id,
            ).model_dump(),
        )

    except RequestValidationError as e:
        logger.warning("Validation error [%s]: %s", request_id, e)
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                message="Invalid request data. Please check your input.",
                error_code="VALIDATION_ERROR",
                timestamp=datetime.utcnow(),
                path=str(request.url.path),
                request_id=request_id,
                details={
                    "validation_errors": [
                        {
                            "field": ".".join(str(x) for x in err["loc"]),
                            "message": err["msg"],
                            "type": err["type"],
                        }
                        for err in e.errors()
                    ]
                },
            ).model_dump(),
        )

    except Exception as e:
        logger.exception("Unexpected error [%s]: %s", request_id, e)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                message="Internal server error. Please contact support if this persists.",
                error_code="INTERNAL_ERROR",
                timestamp=datetime.utcnow(),
                path=str(request.url.path),
                request_id=request_id,
                details={"support_message": "Include this request ID when contacting support"},
            ).model_dump(),
        )
