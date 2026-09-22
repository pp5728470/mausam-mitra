from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Service liveness indicator")
    service: str = Field(default="mausam-mitra-api", description="Service identifier")


class PaginatedMeta(BaseModel):
    total: int
    limit: int
    offset: int


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    meta: PaginatedMeta
