from __future__ import annotations

from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Prompt, AnalysisResult


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
