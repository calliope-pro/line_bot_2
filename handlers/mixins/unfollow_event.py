from typing import List

from linebot.models.events import UnfollowEvent
from pydantic import parse_obj_as

from .base import EventHandlerMixinBase
from models import ReminderModel, ReminderWithKeyModel
from config.settings import DB_LINE_ACCOUNTS, DB_REMINDERS

class UnfollowEventHandlerMixin(EventHandlerMixinBase):
    async def handle_unfollow_event(self, event: UnfollowEvent):
        DB_LINE_ACCOUNTS.delete(self.user_id)
        reminders = parse_obj_as(List[ReminderWithKeyModel], DB_REMINDERS.fetch(ReminderModel.construct(line_user_id=self.user_id).dict(include={'line_user_id'})).items)
        map(lambda reminder: DB_REMINDERS.delete(reminder.key), reminders)
        DB_REMINDERS.delete(self.user_id)
        image_file_paths: List[str] = self.drive.list(prefix=self.user_id)["names"]
        self.drive.delete_many(image_file_paths)
