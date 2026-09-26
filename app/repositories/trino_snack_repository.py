"""Trino database read queries for snack products.

Handles the SQL query paths for product listings and individual item lookups
by utilizing the Trino query engine instead of fetching from MongoDB directly.
"""

import logging
from typing import Any, List, Optional, Tuple

from app.infrastructure.trino_client import run_query
from app.models.snack import Snack

logger = logging.getLogger(__name__)
TABLE = "mongodb.vending_machine.snacks"


def _row_to_snack(row: tuple) -> Snack:
    """Converts a raw Trino database tuple row into a structured Snack model instance."""
    logger.debug("Parsing raw Trino data row into Snack model schema.")
    return Snack(
        id=row[0],
        name=row[1],
        description=row[2],
        price=row[3],
        quantity=row[4],
        sold_out=row[5],
    )


def _build_where_clause(name: Optional[str], sold_out: Optional[bool]) -> Tuple[str, List[Any]]:
    """Generates standard parameterized SQL filter clauses based on active search arguments."""
    clauses = []
    params: List[Any] = []
    if name:
        clauses.append("LOWER(name) LIKE LOWER(?)")
        params.append(f"%{name}%")
    if sold_out is not None:
        clauses.append("sold_out = ?")
        params.append(sold_out)
    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return where_sql, params


def list_all(
    name: Optional[str] = None,
    sold_out: Optional[bool] = None,
    limit: Optional[int] = None,
    offset: int = 0,
) -> List[Snack]:
    """Retrieves a sorted list of snack records from the reporting view using optional pagination parameters.
    
    If limit is None, it scans and returns all matching results without restrictions.
    """
    logger.debug("Executing catalog search list query against the Trino query engine.")
    where_sql, params = _build_where_clause(name, sold_out)
    query = (
        f"SELECT CAST(_id AS VARCHAR), name, description, price, quantity, sold_out "
        f"FROM {TABLE} {where_sql} ORDER BY name"
    )
    if limit is not None:
        query += " OFFSET ? LIMIT  ?"
        params = params + [offset, limit]
    rows = run_query(query, params=tuple(params))
    return [_row_to_snack(row) for row in rows]


def count_all(name: Optional[str] = None, sold_out: Optional[bool] = None) -> int:
    """Counts the total number of snack records matching the current catalog filter criteria."""
    logger.debug("Executing aggregation count query against the Trino query engine.")
    where_sql, params = _build_where_clause(name, sold_out)
    rows = run_query(f"SELECT COUNT(*) FROM {TABLE} {where_sql}", params=tuple(params))
    return rows[0][0]


def get_by_id(snack_id: str) -> Optional[Snack]:
    """Finds and builds a single product instance by executing an explicit ID record search in Trino."""
    logger.debug("Executing individual item query for snack ID: %s against the Trino query engine.", snack_id)
    rows = run_query(
        f"SELECT CAST(_id AS VARCHAR), name, description, price, quantity, sold_out "
        f"FROM {TABLE} WHERE _id = ObjectId(?)",
        params=(snack_id,),
    )
    if not rows:
        return None
    return _row_to_snack(rows[0])
