"""App entrypoint — FastAPI instance, startup/shutdown, health check"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.infrastructure.mongo_client import close_mongo_connection, connect_to_mongo, get_database
from app.infrastructure.trino_client import run_query
from app.routers import products,cash,websocket,analytics,inventory

settings = get_settings()

logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s", settings.app_name)
    connect_to_mongo()
    yield
    logger.info("Shutting down %s", settings.app_name)
    close_mongo_connection()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
register_exception_handlers(app)

app.include_router(products.router)
app.include_router(cash.router)
app.include_router(websocket.router)
app.include_router(analytics.router)
app.include_router(inventory.router)


@app.get("/health", tags=["infra"])
def health() -> dict:
    try:
        get_database().command("ping")
        mongo_status = "ok"
    except Exception:
        logger.exception("MongoDB health check failed")
        mongo_status = "unreachable"

    try:
        run_query("SELECT 1")
        trino_status = "ok"
    except Exception:
        logger.exception("Trino health check failed")
        trino_status = "unreachable"


    overall_status = "ok" if (mongo_status == "ok" and trino_status == "ok") else "degraded"
    return {"status": overall_status, "mongo": mongo_status, "trino": trino_status}
