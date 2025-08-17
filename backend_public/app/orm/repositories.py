from __future__ import annotations

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Prompt, AnalysisResult, AnalysisEvent, EventType


class PromptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, prompt: Prompt) -> Prompt:
        self.session.add(prompt)
        await self.session.commit()
        await self.session.refresh(prompt)
        return prompt

    async def get(self, prompt_id: str) -> Optional[Prompt]:
        return await self.session.get(Prompt, prompt_id)


class AnalysisRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, analysis_id: str) -> Optional[AnalysisResult]:
        res = await self.session.execute(select(AnalysisResult).where(AnalysisResult.id == analysis_id))
        return res.scalar_one_or_none()

    async def add(self, analysis: AnalysisResult) -> AnalysisResult:
        self.session.add(analysis)
        await self.session.commit()
        await self.session.refresh(analysis)
        return analysis

    async def update(self, analysis: AnalysisResult) -> AnalysisResult:
        await self.session.commit()
        await self.session.refresh(analysis)
        return analysis


class EventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, event: AnalysisEvent) -> AnalysisEvent:
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def log(
        self,
        *,
        event_type: EventType,
        analysis_id: Optional[str] = None,
        prompt_id: Optional[str] = None,
        event_data: Optional[dict] = None,
        duration_ms: Optional[int] = None,
        memory_usage_mb: Optional[float] = None,
        request_id: Optional[str] = None,
        user_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AnalysisEvent:
        ev = AnalysisEvent(
            analysis_id=analysis_id,
            prompt_id=prompt_id,
            event_type=event_type,
            event_data=event_data or {},
            duration_ms=duration_ms,
            memory_usage_mb=memory_usage_mb,
            request_id=request_id,
            user_ip=user_ip,
            user_agent=user_agent,
        )
        return await self.add(ev)
