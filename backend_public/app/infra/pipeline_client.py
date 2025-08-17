from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List

import httpx

from ..config import settings

logger = logging.getLogger(__name__)


class PipelineError(Exception):
    """Base pipeline service error"""


class PipelineTimeoutError(PipelineError):
    """Pipeline service timeout error"""


class PipelineHTTPError(PipelineError):
    """Pipeline service HTTP error with status code"""

    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code


class PipelineClient:
    def __init__(self) -> None:
        # Use internal_api_base from settings
        self.base_url = settings.internal_api_base.rstrip("/")
        self.timeout = httpx.Timeout(connect=5.0, read=120.0, write=10.0, pool=5.0)
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            headers={
                "User-Agent": "Curestry-Proxy/1.0",
                "Content-Type": "application/json",
            },
        )

    async def analyze(self, prompt: str, format_type: str = "auto", language: str = "auto") -> Dict[str, Any]:
        payload = {
            "prompt": {"content": prompt, "format_type": format_type, "language": language}
        }

        last_exception: Exception | None = None
        for attempt in range(3):
            try:
                logger.info("Pipeline analyze attempt %s/3", attempt + 1)
                response = await self.client.post(f"{self.base_url}/analyze/", json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException as e:
                last_exception = e
                logger.warning("Pipeline timeout on attempt %s: %s", attempt + 1, e)
                if attempt == 2:
                    raise PipelineTimeoutError(
                        f"Pipeline service timeout after 3 attempts. Analysis taking longer than {self.timeout.read}s."
                    )
                await asyncio.sleep(2**attempt)
            except httpx.HTTPStatusError as e:
                last_exception = e
                status_code = e.response.status_code
                logger.error("Pipeline HTTP error %s on attempt %s", status_code, attempt + 1)
                if 400 <= status_code < 500:
                    raise PipelineHTTPError(
                        f"Pipeline client error {status_code}: {e.response.text}", status_code
                    )
                if status_code >= 500 and attempt < 2:
                    await asyncio.sleep(2**attempt)
                    continue
                raise PipelineHTTPError(
                    f"Pipeline server error {status_code}: {e.response.text}", status_code
                )
            except Exception as e:
                last_exception = e
                logger.error("Pipeline connection error on attempt %s: %s", attempt + 1, e)
                if attempt == 2:
                    raise PipelineError(f"Pipeline connection failed after 3 attempts: {str(e)}")
                await asyncio.sleep(2**attempt)

        raise PipelineError(f"Unexpected error after retries: {last_exception}")

    async def analyze_with_context(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send enriched payload for analysis. Gracefully falls back to the simpler
        analyze() call if the upstream does not accept the payload (e.g., 404/405)
        or returns 4xx client validation errors that indicate unsupported fields.
        """
        last_exception: Exception | None = None
        for attempt in range(3):
            try:
                logger.info("Pipeline analyze_with_context attempt %s/3", attempt + 1)
                response = await self.client.post(f"{self.base_url}/analyze/", json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                last_exception = e
                status_code = e.response.status_code
                # Fallback on 404/405 or validation 400 that likely means unsupported shape
                if status_code in (404, 405) or (status_code == 400 and "unsupported" in e.response.text.lower()):
                    p = payload.get("prompt", {})
                    return await self.analyze(
                        prompt=p.get("content", ""),
                        format_type=p.get("format_type", "auto"),
                        language=p.get("language", "auto"),
                    )
                if 400 <= status_code < 500:
                    raise PipelineHTTPError(
                        f"Pipeline client error {status_code}: {e.response.text}", status_code
                    )
                if status_code >= 500 and attempt < 2:
                    await asyncio.sleep(2**attempt)
                    continue
                raise PipelineHTTPError(
                    f"Pipeline server error {status_code}: {e.response.text}", status_code
                )
            except httpx.TimeoutException as e:
                last_exception = e
                if attempt == 2:
                    raise PipelineTimeoutError(
                        f"Pipeline service timeout after 3 attempts. Analysis taking longer than {self.timeout.read}s."
                    )
                await asyncio.sleep(2**attempt)
            except Exception as e:
                last_exception = e
                if attempt == 2:
                    # Final fallback to simple analyze if possible
                    p = payload.get("prompt", {})
                    return await self.analyze(
                        prompt=p.get("content", ""),
                        format_type=p.get("format_type", "auto"),
                        language=p.get("language", "auto"),
                    )
                await asyncio.sleep(2**attempt)

    async def clarify(self, analysis_id: str, answers: List[Dict]) -> Dict[str, Any]:
        payload = {"prompt_id": analysis_id, "answers": answers}
        for attempt in range(3):
            try:
                response = await self.client.post(f"{self.base_url}/analyze/clarify", json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                if attempt == 2:
                    raise PipelineError(f"Clarify failed: {str(e)}")
                await asyncio.sleep(2**attempt)

    async def apply_patches(self, analysis_id: str, patch_ids: List[str]) -> Dict[str, Any]:
        payload = {"prompt_id": analysis_id, "patch_ids": patch_ids}
        for attempt in range(3):
            try:
                response = await self.client.post(f"{self.base_url}/analyze/apply", json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                if attempt == 2:
                    raise PipelineError(f"Apply patches failed: {str(e)}")
                await asyncio.sleep(2**attempt)

    async def health_check(self) -> bool:
        try:
            response = await self.client.get(f"{self.base_url}/healthz", timeout=httpx.Timeout(5.0))
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        await self.client.aclose()


async def get_pipeline_client() -> PipelineClient:
    return PipelineClient()
