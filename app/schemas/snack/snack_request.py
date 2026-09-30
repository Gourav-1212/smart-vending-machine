from pydantic import BaseModel,field_validator,Field
from typing import Optional

class AddSnackRequest(BaseModel):
    name: str = Field(..., description="The name of the new snack item")
    description: str = Field(..., description="Short details about the item")
    price: int = Field(..., gt=0, description="Price in minor currency units")
    quantity: int = Field(..., ge=0, description="Initial stock quantity to load")
    low_stock_threshold: int = Field(default=3,ge=0,description="minimum stock limit before low-stock warning")

    @field_validator("name", "description", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strips leading/trailing whitespace and rejects strings that are blank after stripping."""
        if isinstance(v, str):
            v = v.strip()
        return v

class RestockRequest(BaseModel):
    quantity: int = Field(..., gt=0, description="Number of items to add to inventory")
    low_stock_threshold: Optional[int]= Field(default=None, ge=0, description="optional new low stock threshold")