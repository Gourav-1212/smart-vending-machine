from typing import Dict
from pydantic import BaseModel, Field,field_validator

class RefillRequest(BaseModel):
    denominations: Dict[int, int] = Field(..., description="Map of coin/note denominations to count")

    @field_validator("denominations")
    @classmethod
    def must_not_be_empty(cls, v: Dict[int, int]) -> Dict[int, int]:
        """Rejects an empty denominations map so silent no-op refills are never accepted."""
        if not v:
            raise ValueError("denominations must not be empty — provide at least one denomination")
        return v