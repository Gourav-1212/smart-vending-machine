
from pydantic import BaseModel

class SystemSetting(BaseModel):
    key: str
    threshold: int
