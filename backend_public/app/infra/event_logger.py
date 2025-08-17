from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..orm.models import AnalysisEvent, EventType

logger = logging.getLogger(__name__)


class EventLogger:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_event(
        self,
        event_type: EventType,
        analysis_id: Optional[str] = None,
        prompt_id: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None,
        memory_usage_mb: Optional[float] = None,
        request_id: Optional[str] = None,
        user_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AnalysisEvent:
        """Log analysis event to database"""

        event = AnalysisEvent(
            analysis_id=analysis_id,
            prompt_id=prompt_id,
            event_type=event_type,
            event_data=event_data or {},
            duration_ms=duration_ms,
            memory_usage_mb=memory_usage_mb,
            request_id=request_id,
            user_ip=user_ip,
            user_agent=user_agent,
            timestamp=datetime.utcnow(),
        )

        self.session.add(event)

        try:
            await self.session.commit()
            logger.info("Event logged: %s for analysis %s", event_type, analysis_id)
            return event
        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to log event %s: %s", event_type, e)
            raise
