from typing import Dict
from pydantic import BaseModel, Field

class RefillRequest(BaseModel):
    denominations: Dict[int, int] = Field(..., description="Map of coin/note denominations to count")