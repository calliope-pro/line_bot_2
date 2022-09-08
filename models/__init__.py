from typing import List, Optional
from pydantic import BaseModel

class KeyModelMixin(BaseModel):
    key: str

class PushContentModel(BaseModel):
    type: Optional[str] = None
    body: str

class UserModel(BaseModel):
    token: str
    mode: str
    memos: List[str]

class UserWithKeyModel(UserModel, KeyModelMixin):
    pass
