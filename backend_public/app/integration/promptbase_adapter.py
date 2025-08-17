from __future__ import annotations

from typing import Any, Dict, Optional

from ..dto.requests import AnalyzeRequest


def build_analyze_payload(req: AnalyzeRequest) -> Dict[str, Any]:
    """
    Build a richer payload for prompt-base that includes:
    - prompt content/format/language
    - client info (type/name/version/metadata) if present
    - future: user/session identifiers when available
    """
    payload: Dict[str, Any] = {
        "prompt": {
            "content": req.prompt.content,
            "format_type": req.prompt.format_type,
            "language": req.prompt.language,
        }
    }

    if req.client_info:
        payload["client_info"] = req.client_info.model_dump()

    # Hooks for future deep integration (user/session)
    # if req.user_id: payload["user_id"] = req.user_id
    # if req.session_id: payload["session_id"] = req.session_id

    return payload
