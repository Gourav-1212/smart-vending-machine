from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class SnackMinimal(BaseModel):
    """Fewer fields - Perfect for listing multiple products quickly."""
    id: Optional[str] = Field(default=None, validation_alias="_id")
    name: str
    price: int
    

    model_config = {"populate_by_name": True}


class SnackDetailed(SnackMinimal):
    """More fields - Automatically includes all fields from SnackMinimal plus these details."""
    sold_out: bool = False
    description: str
    quantity: int
    created_at: datetime
    updated_at: datetime

class AddSnackRequest(BaseModel):
    name: str = Field(..., description="The name of the new snack item")
    description: str = Field(..., description="Short details about the item")
    price: int = Field(..., gt=0, description="Price in minor currency units")
    quantity: int = Field(..., ge=0, description="Initial stock quantity to load")

class RestockRequest(BaseModel):
    quantity: int = Field(..., gt=0, description="Number of items to add to inventory")
