from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

T = TypeVar("T")


class Result(BaseModel, Generic[T]):
    """Result pattern for success/failure responses."""

    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    metadata: Optional[dict] = None

    @classmethod
    def ok(cls, data: T, metadata: Optional[dict] = None) -> "Result[T]":
        return cls(success=True, data=data, metadata=metadata)

    @classmethod
    def fail(
        cls, message: str, code: str = "GENERIC_ERROR", metadata: Optional[dict] = None
    ) -> "Result[T]":
        return cls(success=False, error=message, error_code=code, metadata=metadata)


class ErrorResponse(BaseModel):
    """Standard API error format."""

    message: str
    error_code: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    path: Optional[str] = None
    request_id: Optional[str] = None
    details: Optional[dict] = None


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ClientType(str, Enum):
    BROWSER = "browser"
    IDE = "ide"
    CLI = "cli"
    API = "api"


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=1000)


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    limit: int
    pages: int

    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @property
    def has_prev(self) -> bool:
        return self.page > 1
