from typing import Dict
from pydantic import BaseModel

class DenominationsResponse(BaseModel):
    denominations: Dict[int, int]
