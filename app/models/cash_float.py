"""CashFloat model — denomination counts the machine currently holds"""

from datetime import datetime, timezone
from typing import Dict, Optional

from pydantic import BaseModel, Field


class CashFloat(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    denominations: Dict[int, int]
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
