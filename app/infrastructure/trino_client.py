"""Trino connection — the single place a Trino connection is opened.
Mirrors mongo_client.py's role, but for the read-only SQL path (products,
status, and later analytics)."""

import logging
from typing import Any, List, Sequence, Tuple

import trino

from app.core.config import get_settings
from app.core.exceptions import TrinoUnavailableError

logger = logging.getLogger(__name__)


def run_query(query: str, params: Sequence[Any] = ()) -> List[Tuple]:
    """Runs a SQL query against Trino and returns all rows.

    A fresh connection is opened per query rather than kept open, since
    our read volume here is low and this avoids managing a long-lived
    connection's lifecycle. Any failure — connection refused, timeout,
    bad query — is caught here and turned into TrinoUnavailableError, so
    nothing above this function ever sees a raw driver exception or a
    hanging request."""
    settings = get_settings()

    conn=None
    cursor=None

    try:
        conn = trino.dbapi.connect(
            host=settings.trino_host,
            port=settings.trino_port,
            user=settings.trino_user,
            catalog=settings.trino_catalog,
            schema=settings.trino_schema,
            http_scheme="http",
            request_timeout=settings.trino_connect_timeout_seconds,
        )
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return rows
    except Exception:
        logger.error("Trino query failed")
        raise TrinoUnavailableError(
            "Trino unavailable",
            reason="Could not reach Trino to complete this request",
        )
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                logger.warning("Failed to close Trino cursor")
        if conn is not None:
            try:
                conn.close()
            except Exception:
                logger.warning("Failed to close Trino connection")
