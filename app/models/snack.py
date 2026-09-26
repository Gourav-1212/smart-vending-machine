"""Snack model"""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class Snack(BaseModel):
    id: Optional[str] = Field(default=None,  validation_alias="_id")
    name: str
    description: str
    price: int
    quantity: int
    sold_out: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
