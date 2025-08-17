from pydantic import BaseModel, Field
from typing import Optional, Any, List
from datetime import datetime

class UserOut(BaseModel):
    id: int
    email: Optional[str]
    name: Optional[str]
    avatar_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class MetricPoint(BaseModel):
    run_id: int
    node_key: Optional[str] = None
    metric_name: str
    metric_value: float
    metric_meta: Optional[dict] = None
    created_at: Optional[datetime] = None

class MetricSeries(BaseModel):
    metric_name: str
    points: List[MetricPoint]

class MetricAggregatePoint(BaseModel):
    ts: datetime
    value: float

class CreateRunIn(BaseModel):
    prompt: Optional[str] = None
    language: Optional[str] = None
    meta: Optional[dict] = None

class RunOut(BaseModel):
    id: int
    status: str
    started_at: datetime
    finished_at: Optional[datetime]

    class Config:
        from_attributes = True

class NodeReportIn(BaseModel):
    status: Optional[str] = Field(default=None)
    result: Optional[dict] = Field(default=None)

class MetricsReportIn(BaseModel):
    metrics: List[MetricPoint]
