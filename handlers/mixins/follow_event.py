from uuid import uuid4

from linebot.models.events import FollowEvent
from linebot.models.send_messages import TextSendMessage

from config.settings import DB_LINE_ACCOUNTS, PostbackActionData
from models import UserModel

from .base import EventHandlerMixinBase


class FollowEventHandlerMixin(EventHandlerMixinBase):
    async def handle_follow_event(self, event: FollowEvent):
        DB_LINE_ACCOUNTS.put(
            UserModel(
                token=str(uuid4()),
                mode=PostbackActionData.normal.value,
                memos=[],
                storage_capacity=0,
            ).dict(),
            key=self.user_id,
        )

        await self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="友達追加ありがとうございます。詳しい使い方は画面下部のリッチメニュー内の「取扱説明書」をご覧ください。"),
        )
