import logging
from datetime import date

from fastapi import APIRouter, Query,Depends
from app.core.security import require_api_key

from app.schemas.analytics import (
    DailyInventorySnapshotRangeResponse,
    DailyInventorySnapshotResponse,
)
from app.services import inventory_snapshot

logger = logging.getLogger(__name__)

router = APIRouter(tags=["snapshoot"], dependencies=[Depends(require_api_key)])


@router.get(
    "/analytics/daily-snapshots",
    response_model=DailyInventorySnapshotRangeResponse,
)
def get_daily_snapshots(
    start: date = Query(
        ..., description="Start date (inclusive), format: YYYY-MM-DD"
    ),
    end: date = Query(
        ..., description="End date (inclusive), format: YYYY-MM-DD"
    ),
) -> DailyInventorySnapshotRangeResponse:
    """Serves aggregated daily inventory and cash status reports across a date
    range.

    Queries the inventory_snapshots MongoDB collection (written by the
    scheduled Airflow DAG).
    """
    logger.info(
        "Received daily snapshots report request: start=%s end=%s", start, end
    )
    return inventory_snapshot.get_snapshots_by_range(start=start, end=end)


@router.get(
    "/analytics/daily-snapshots/{snapshot_date}",
    response_model=DailyInventorySnapshotResponse,
)
def get_daily_snapshot_by_date(
    snapshot_date: date,
) -> DailyInventorySnapshotResponse:
    """Retrieves a single day's pre-aggregated inventory and cash status snapshot
    from MongoDB.
    """
    logger.info(
        "Received single daily snapshot request for date: %s", snapshot_date
    )
    return inventory_snapshot.get_snapshot_by_date(snapshot_date)
