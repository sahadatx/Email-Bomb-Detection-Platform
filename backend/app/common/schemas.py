from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
    """
    Base Pydantic model for API schemas.
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class APIMessage(APIModel):
    message: str


class HealthResponse(APIModel):
    status: str
    service: str
    version: str
    environment: str


class ErrorDetail(APIModel):
    code: str
    message: str
    details: object | None = None


class ErrorResponse(APIModel):
    success: bool = False
    error: ErrorDetail


T = TypeVar("T")


class PaginatedResponse(APIModel, Generic[T]):
    items: list[T]

    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    pages: int = Field(ge=0)