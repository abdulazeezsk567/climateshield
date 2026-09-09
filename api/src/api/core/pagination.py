"""Generic pagination schemas and slicing utilities for list endpoints."""

import math
from typing import Generic, List, Sequence, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized envelope for paginated collections."""
    items: List[T] = Field(..., description="Array of records for the current page")
    total_items: int = Field(..., ge=0, description="Total count of available matching items")
    page: int = Field(..., ge=1, description="Current 1-indexed page number")
    page_size: int = Field(..., ge=1, description="Maximum items per page")
    total_pages: int = Field(..., ge=0, description="Total calculated pages")
    has_next: bool = Field(..., description="Whether a subsequent page exists")
    has_prev: bool = Field(..., description="Whether a preceding page exists")


def paginate_items(
    items: Sequence[T],
    page: int = 1,
    page_size: int = 20,
) -> PaginatedResponse[T]:
    """Slice an in-memory or queried sequence into a PaginatedResponse envelope.

    Args:
        items: Full sequence of candidate items.
        page: Requested page number (1-indexed).
        page_size: Maximum items per page.

    Returns:
        Structured PaginatedResponse instance.
    """
    total_items = len(items)
    page_size = max(1, min(100, page_size))  # Clamp page_size to [1, 100]
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0

    page = max(1, page)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    page_items = list(items[start_idx:end_idx]) if start_idx < total_items else []

    return PaginatedResponse[T](
        items=page_items,
        total_items=total_items,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1 and total_pages > 0,
    )
