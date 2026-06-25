from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    skip: int
    limit: int


class MessageResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str = "0.1.0"
