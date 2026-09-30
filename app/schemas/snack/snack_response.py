from datetime import datetime
from pydantic import BaseModel, Field

class SnackMinimal(BaseModel):
    """Fewer fields - Perfect for listing multiple products quickly."""
    id: str = Field(default=None, validation_alias="_id")
    name: str
    price: int
    

    model_config = {"populate_by_name": True}


class SnackDetailed(SnackMinimal):
    """More fields - Automatically includes all fields from SnackMinimal plus these details."""
    sold_out: bool = False
    description: str
    quantity: int
    low_stock_threshold: int