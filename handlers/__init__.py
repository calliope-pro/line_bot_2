import os
from typing import List, Optional

from deta import _Drive
from linebot import AsyncLineBotApi
from linebot.models.events import (
    Event,
    FollowEvent,
    MessageEvent,
    PostbackEvent,
    UnfollowEvent,
)
from linebot.models.send_messages import TextSendMessage

from config.settings import IS_MAINTENANCE

from .mixins.follow_event import FollowEventHandlerMixin
from .mixins.message_event import MessageEventHandlerMixin
from .mixins.postback_event import PostbackEventHandlerMixin
from .mixins.unfollow_event import UnfollowEventHandlerMixin


class EventsHandler(
    FollowEventHandlerMixin,
    UnfollowEventHandlerMixin,
    MessageEventHandlerMixin,
    PostbackEventHandlerMixin,
):
    events: List[Event]
    user_id: Optional[str]

    def __init__(
        self, line_bot_api: AsyncLineBotApi, events: List[Event], drive: _Drive
    ):
        self.line_bot_api = line_bot_api
        self.events = events
        self.drive = drive
        self.user_id = None

    async def handle(self):
        # ベント処理List[Event]
        for event in self.events:
            if IS_MAINTENANCE:
                try:
                    assert (
                        event.source.user_id == os.environ["MY_LINE_USER_ID"]
                    ), "user_idが異なります"
                except AssertionError:
                    await self.line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="Not available due to maintenance."),
                    )
                    break

            self.user_id = event.source.user_id

            # メッセージイベント
            if isinstance(event, MessageEvent):
                await self.handle_message_event(event)
                break
            # ポストバックイベント
            elif isinstance(event, PostbackEvent):
                await self.handle_postback_event(event)
                break
            # 友達追加イベント
            elif isinstance(event, FollowEvent):
                await self.handle_follow_event(event)
                break
            # 友達解除イベント
            elif isinstance(event, UnfollowEvent):
                await self.handle_unfollow_event(event)
                break
