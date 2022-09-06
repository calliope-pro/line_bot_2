from typing import Optional
from pydantic import BaseModel

class PushContentModel(BaseModel):
    type: Optional[str] = None
    body: str