from uuid import uuid4

from linebot.models.events import FollowEvent
from linebot.models.send_messages import TextSendMessage

from config.settings import DB_LINE_ACCOUNTS, PostbackActionData
from models import UserModel

from .base import EventHandlerMixinBase


class FollowEventHandlerMixin(EventHandlerMixinBase):
    async def handle_follow_event(self, event: FollowEvent):
        DB_LINE_ACCOUNTS.put(
            UserModel().dict(),
            key=self.user_id,
        )

        await self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="Welcome!"),
        )
