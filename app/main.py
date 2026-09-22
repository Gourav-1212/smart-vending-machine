"""App entrypoint — FastAPI instance, startup/shutdown, health check"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.infrastructure.mongo_client import close_mongo_connection, connect_to_mongo, get_database
from app.routers import products,purchase,admin,websocket

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
app.include_router(purchase.router)
app.include_router(admin.router)
app.include_router(websocket.router)


@app.get("/health", tags=["infra"])
def health() -> dict:
    try:
        get_database().command("ping")
        mongo_status = "ok"
    except Exception:
        logger.exception("MongoDB health check failed")
        mongo_status = "unreachable"

    return {"status": "ok", "mongo": mongo_status}
