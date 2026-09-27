"""Analytics service — handles revenue and top-seller reporting over a date range."""


import logging
from datetime import date


from app.core.exceptions import ValidationError
from app.repositories import trino_sale_repository
from app.schemas.analytics import RevenueResponse, TopSellerItem, TopSellersResponse


logger = logging.getLogger(__name__)




def get_revenue(start: date, end: date) -> RevenueResponse:
    """Returns total revenue and units sold between start and end dates (inclusive).


    Raises ValidationError if the date range is invalid (end before start).
    """
    logger.info("Fetching revenue analytics from %s to %s.", start, end)


    if end < start:
        raise ValidationError(
            "Invalid date range",
            reason="end date must be on or after start date",
        )


    total_revenue, total_units_sold = trino_sale_repository.get_revenue(start, end)


    logger.info("Revenue analytics complete: revenue=%d units=%d", total_revenue, total_units_sold)
    return RevenueResponse(
        start=start,
        end=end,
        total_revenue=total_revenue,
        total_units_sold=total_units_sold,
    )




def get_top_sellers(start: date, end: date, limit: int) -> TopSellersResponse:
    """Returns snacks ranked by total revenue within the given date range.


    Raises ValidationError if the date range is invalid (end before start).
    """
    logger.info("Fetching top-sellers analytics from %s to %s (limit=%d).", start, end, limit)


    if end < start:
        raise ValidationError(
            "Invalid date range",
            reason="end date must be on or after start date",
        )


    rows = trino_sale_repository.get_top_sellers(start, end, limit)


    sellers = [
        TopSellerItem(
            rank=index + 1,
            snack_name=snack_name,
            total_revenue=total_revenue,
            units_sold=units_sold,
        )
        for index, (snack_name, total_revenue, units_sold) in enumerate(rows)
    ]


    logger.info("Top-sellers analytics complete: %d results returned.", len(sellers))
    return TopSellersResponse(start=start, end=end, sellers=sellers)