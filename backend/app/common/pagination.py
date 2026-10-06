from math import ceil

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Standard pagination parameters."""

    page: int = Field(
        default=1,
        ge=1,
    )

    page_size: int = Field(
        default=30,
        ge=1,
        le=100,
    )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def calculate_pages(
    total: int,
    page_size: int,
) -> int:
    """Calculate total pages."""

    if total <= 0:
        return 0

    return ceil(total / page_size)