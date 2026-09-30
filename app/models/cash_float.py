"""CashFloat model — denomination counts the machine currently holds"""

from datetime import datetime, timezone
from typing import Dict, Optional

from pydantic import BaseModel, Field


class CashFloat(BaseModel):
    id: Optional[str] = Field(default=None,  validation_alias="_id")
    denominations: Dict[int, int]
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}

    @property
    def total_cash(self) -> int:
        """Dynamically calculates the total monetary value in the vault.

        Multiplies each denomination (key) by its quantity (value) and sums
        them up.
        """
        return sum(denom * qty for denom, qty in self.denominations.items())
