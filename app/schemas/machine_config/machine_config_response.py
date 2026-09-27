from pydantic import BaseModel
class ThresholdResponse(BaseModel):
    low_stock_threshold: int

class ThresholdUpdateResponse(BaseModel):
    status: str
    updated_threshold: int