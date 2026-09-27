"""Analytics router — revenue and top-seller reporting endpoints for the operator."""


import logging
from datetime import date


from fastapi import APIRouter, Depends, Query


from app.core.security import require_api_key
from app.schemas.analytics import RevenueResponse, TopSellersResponse
from app.services import analytics_service


logger = logging.getLogger(__name__)


router = APIRouter(tags=["analytics"], dependencies=[Depends(require_api_key)])




@router.get("/analytics/revenue", response_model=RevenueResponse)
def get_revenue(
    start: date = Query(..., description="Start date (inclusive), format: YYYY-MM-DD"),
    end: date = Query(..., description="End date (inclusive), format: YYYY-MM-DD"),
) -> RevenueResponse:
    """Returns total revenue and units sold within the given date range.


    Both dates are inclusive. Queries the sales collection via Trino.
    Returns a clear 503 if Trino is unavailable rather than hanging.
    """
    logger.info("Received revenue analytics request: start=%s end=%s", start, end)
    result = analytics_service.get_revenue(start=start, end=end)
    logger.info("Revenue analytics request completed successfully.")
    return result




@router.get("/analytics/top-sellers", response_model=TopSellersResponse)
def get_top_sellers(
    start: date = Query(..., description="Start date (inclusive), format: YYYY-MM-DD"),
    end: date = Query(..., description="End date (inclusive), format: YYYY-MM-DD"),
    limit: int = Query(default=5, ge=1, le=20, description="Number of top sellers to return"),
) -> TopSellersResponse:
    """Returns snacks ranked by total revenue within the given date range.


    Results are ordered from highest to lowest revenue. Limit controls
    how many entries are returned (default 5, max 20).
    Queries the sales collection via Trino.
    """
    logger.info(
        "Received top-sellers analytics request: start=%s end=%s limit=%d", start, end, limit
    )
    result = analytics_service.get_top_sellers(start=start, end=end, limit=limit)
    logger.info("Top-sellers analytics request completed successfully.")
    return result

