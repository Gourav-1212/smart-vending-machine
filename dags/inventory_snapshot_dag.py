"""Airflow DAG: Periodic Inventory & Cash Float Snapshot Orchestrator

Triggers the FastAPI application service layer pipeline to take clean, 
fully validated inventory snapshots using dynamic per-snack metrics.
"""

from datetime import datetime, timedelta
import logging
import os

from airflow import DAG
from airflow.operators.python import PythonOperator

from app.infrastructure.mongo_client import connect_to_mongo, close_mongo_connection
from app.services.inventory_snapshot import compute_and_save_daily_snapshot

logger = logging.getLogger(__name__)

SCHEDULE_INTERVAL = os.getenv("AIRFLOW_SNAPSHOT_SCHEDULE", "*/15 * * * *")


def record_inventory_snapshot(**kwargs):
    """Orchestrates the inventory capture task by initializing database connections and executing service logic."""
    target_date_str = kwargs.get("ds")
    
    if not target_date_str:
        target_date_str = datetime.now().strftime("%Y-%m-%d")

    logger.info("Initializing application layer MongoDB client within Airflow runtime context.")
    connect_to_mongo()

    try:
        logger.info("Executing application layer inventory snapshot pipeline for logical date: %s", target_date_str)
        saved_snapshot = compute_and_save_daily_snapshot(target_date_str=target_date_str)
        
        logger.info(
            "Successfully produced snapshot via application layer for %s: %d total items, %d total cash.",
            saved_snapshot.snapshot_date,
            saved_snapshot.total_items,
            saved_snapshot.total_cash,
        )
    finally:
        logger.info("Closing application layer MongoDB connection pool inside task lifecycle end.")
        close_mongo_connection()


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="inventory_snapshot_dag",
    default_args=default_args,
    description="Periodic inventory and cash float snapshot into MongoDB via Application Layer",
    schedule_interval=SCHEDULE_INTERVAL,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["vending_machine", "inventory", "snapshot"],
) as dag:

    snapshot_task = PythonOperator(
        task_id="take_inventory_snapshot",
        python_callable=record_inventory_snapshot,
        provide_context=True,
    )
