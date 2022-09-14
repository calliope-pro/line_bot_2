from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from config.settings import PostbackActionData


class KeyModelMixin(BaseModel):
    key: str


class PushContentModel(BaseModel):
    type: Optional[str] = None
    body: str


class ReminderModel(BaseModel):
    datetime: str
    content: str
    line_user_id: str


class ReminderWithKeyModel(ReminderModel, KeyModelMixin):
    pass


class UserModel(BaseModel):
    token: str = Field(default_factory=lambda: str(uuid4()))
    mode: str = PostbackActionData.normal.value
    memos: List[str] = []
    storage_capacity: int = 0


class UserWithKeyModel(UserModel, KeyModelMixin):
    pass
