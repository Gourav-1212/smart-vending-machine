from pydantic import BaseModel,Field
class ThresholdUpdateRequest(BaseModel):
    low_stock_threshold: int = Field(..., ge=0, description="New count limit to trigger low stock warnings")