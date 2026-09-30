"""Response schemas for the analytics endpoints."""


from datetime import date
from typing import List


from pydantic import BaseModel




class RevenueResponse(BaseModel):
    """Response for GET /analytics/revenue — total revenue and units sold in a date range."""


    start: date
    end: date
    total_revenue: int
    total_units_sold: int




class TopSellerItem(BaseModel):
    """A single snack entry in the top-sellers ranked list."""


    rank: int
    snack_name: str
    total_revenue: int
    units_sold: int




class TopSellersResponse(BaseModel):
    """Response for GET /analytics/top-sellers — snacks ranked by revenue in a date range."""


    start: date
    end: date
    sellers: List[TopSellerItem]

