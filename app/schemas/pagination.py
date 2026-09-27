"""
Simplified shared pagination utility module.

Provides a unified query-parameter dependency and a reusable response envelope
to standardize item collection paging logic across all endpoints.
"""

import math
from typing import Generic, List, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


def get_pagination(
    page: int = Query(default=1, ge=1, description="Page number, starting at 1"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
):
    """
    FastAPI dependency function to parse and validate pagination input.
    
    Extracts raw parameters directly from the request URL, enforces safe range bounds,
    and returns a tuple containing the page, page size, and calculated SQL offset.
    """
    offset = (page - 1) * page_size
    return page, page_size, offset


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic response envelope schema for wrapping multi-item lists.
    
    Standardizes structural data fields sent back to client applications
    and handles metadata page calculations automatically upon instantiation.
    """
    items: List[T]
    page: int
    page_size: int
    total_items: int
    total_pages: int

    def __init__(self, **data):
        """
        Custom constructor to intercept initialization data.
        
        Extracts structural properties and automatically applies ceiling division 
        to calculate total pages, eliminating the need for a separate factory method.
        """
        total_items = data.get("total_items", 0)
        page_size = data.get("page_size", 20)
        data["total_pages"] = math.ceil(total_items / page_size) if total_items > 0 else 0
        super().__init__(**data)
