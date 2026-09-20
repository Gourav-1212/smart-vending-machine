"""MongoDB connection setup and transaction helper"""

import logging
from contextlib import contextmanager
from typing import Generator, Optional

from pymongo import MongoClient
from pymongo.client_session import ClientSession
from pymongo.database import Database

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_client: Optional[MongoClient] = None

def connect_to_mongo() -> None:
    global _client
    settings = get_settings()
    try:
        _client = MongoClient(settings.mongo_uri)
        _client.admin.command("ping")
    except Exception:
        logger.critical("Could not connect to MongoDB — check MONGO_URI and network access")
        raise
    logger.info("Connected to MongoDB")


def close_mongo_connection() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("MongoDB connection closed")


def get_database() -> Database:
    if _client is None:
        raise RuntimeError("MongoDB client not initialized")
    settings = get_settings()
    return _client[settings.mongo_db_name]


@contextmanager
def start_transaction() -> Generator[ClientSession,None,None]:
    if _client is None:
        raise RuntimeError("MongoDB client not initialized")
    with _client.start_session() as session:
        with session.start_transaction():
            yield session
