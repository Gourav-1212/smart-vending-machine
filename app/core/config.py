"""App settings, loaded from environment variables / .env"""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Smart Vending Machine API"
    app_port: int = Field(default=8000)
    log_level: str = Field(default="DEBUG")

    mongo_uri: str 
    mongo_db_name: str = Field(default="vending_machine")

    trino_host: str = Field(default="localhost")
    trino_port: int = Field(default=8080)
    trino_user: str = Field(default="vending_api")
    trino_catalog: str = Field(default="mongodb")
    trino_schema: str = Field(default="vending_machine")
    trino_connect_timeout_seconds: float = Field(default=3.0)
    trino_query_timeout_seconds: float = Field(default=5.0)

    operator_api_key: str

    low_stock_threshold: int = Field(default=3)
    denominations: List[int]

    ws_path: str = Field(default="/ws/inventory")

    airflow_snapshot_schedule: str = Field(default="*/15 * * * *")

    seed_snack_count: int = Field(default=12)
    seed_backdated_days: int = Field(default=30)
    seed_opening_float_multiplier: int = Field(default=50)


@lru_cache
def get_settings() -> Settings:
    return Settings()
