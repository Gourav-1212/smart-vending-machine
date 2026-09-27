"""Trino read queries for the sales collection.


Handles all analytics SQL — revenue totals and top-seller rankings.
All date filtering is done against the sold_at timestamp field.
"""


import logging
from datetime import date
from typing import List, Tuple


from app.infrastructure.trino_client import run_query


logger = logging.getLogger(__name__)


TABLE = "mongodb.vending_machine.sales"




def get_revenue(start: date, end: date) -> Tuple[int, int]:
    """Returns (total_revenue, total_units_sold) for sales within the date range (inclusive).


    Casts the stored sold_at timestamp to a date before comparing so that
    a sale at 23:59 on the end date is still included.
    """
    logger.debug("Running Trino revenue aggregation query from %s to %s.", start, end)


    query = (
        f"SELECT COALESCE(SUM(total_amount), 0), COALESCE(SUM(quantity), 0) "
        f"FROM {TABLE} "
        f"WHERE CAST(sold_at AS DATE) >= DATE '{start}' "
        f"AND CAST(sold_at AS DATE) <= DATE '{end}'"
    )
    rows = run_query(query)


    total_revenue = int(rows[0][0]) if rows else 0
    total_units_sold = int(rows[0][1]) if rows else 0


    logger.debug("Revenue query result: revenue=%d units=%d", total_revenue, total_units_sold)
    return total_revenue, total_units_sold




def get_top_sellers(start: date, end: date, limit: int) -> List[Tuple[str, int, int]]:
    """Returns a ranked list of (snack_name, total_revenue, units_sold) ordered by revenue descending.


    Each tuple maps directly to one TopSellerItem in the response.
    """
    logger.debug(
        "Running Trino top-sellers query from %s to %s with limit %d.", start, end, limit
    )


    query = (
        f"SELECT snack_name_at_sale, "
        f"SUM(total_amount) AS total_revenue, "
        f"SUM(quantity) AS units_sold "
        f"FROM {TABLE} "
        f"WHERE CAST(sold_at AS DATE) >= DATE '{start}' "
        f"AND CAST(sold_at AS DATE) <= DATE '{end}' "
        f"GROUP BY snack_name_at_sale "
        f"ORDER BY total_revenue DESC "
        f"LIMIT ?"
    )
    rows = run_query(query,params=(limit,))


    logger.debug("Top-sellers query returned %d rows.", len(rows))
    return [(row[0], int(row[1]), int(row[2])) for row in rows]