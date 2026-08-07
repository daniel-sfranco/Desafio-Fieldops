from typing import Generic, List, Optional, Dict, Any, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class FlxErrorBody(BaseModel):
    code: str
    message: str
    flxTraceId: str
    details: Optional[Dict[str, Any]] = Field(default_factory=dict)


class FlxErrorResponse(BaseModel):
    error: FlxErrorBody


class PaginationMeta(BaseModel):
    page: int = Field(ge=1, default=1)
    limit: int = Field(ge=1, le=100, default=20)
    total: int = Field(ge=0, default=0)
    totalPages: int = Field(ge=0, default=0)


class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    meta: PaginationMeta


class HealthResponse(BaseModel):
    status: str = "ok"
    apiRevision: str = "2026.2"
    service: str = "fieldops-lite"
