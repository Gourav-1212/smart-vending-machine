"""Sale model — one record per completed purchase"""

from datetime import datetime, timezone
from typing import Dict, Optional

from pydantic import BaseModel, Field


class Sale(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    snack_id: str
    snack_name_at_sale: str
    unit_price_at_sale: int
    cash_received: int
    change_given: Dict[int, int]
    sold_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
