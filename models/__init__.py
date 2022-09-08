from typing import Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel

class KeyModelMixin(BaseModel):
    key: str

class PushContentModel(BaseModel):
    type: Optional[str] = None
    body: str

class ReminderModel(BaseModel):
    datetime: datetime
    content: str
    line_user_id: str

class ReminderWithKeyModel(ReminderModel, KeyModelMixin):
    pass

class UserModel(BaseModel):
    token: str
    mode: str
    memos: List[str]

class UserWithKeyModel(UserModel, KeyModelMixin):
    pass
