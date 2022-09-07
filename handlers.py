import os
import re
from typing import List
from uuid import uuid4

from cryptocode import decrypt, encrypt
from deta import _Base, _Drive
from linebot import AsyncLineBotApi
from linebot.models.actions import PostbackAction
from linebot.models.events import Event, MessageEvent, FollowEvent, PostbackEvent
from linebot.models.send_messages import TextSendMessage, QuickReply, QuickReplyButton

from settings import BASE_PROJECT_URL

class EventsHandler:
    def __init__(self, line_bot_api: AsyncLineBotApi, events: List[Event], db: _Base, drive: _Drive):
        self.line_bot_api = line_bot_api
        self.events = events
        self.db = db
        self.drive = drive
        self.user_id = None

    async def handle_message_event(self, event: MessageEvent):
        user_token = self.db.get(self.user_id)['token']
        if event.message.type == 'image':
            data = await self.line_bot_api.get_message_content(event.message.id)
            binary_data = b''
            async for b in data.iter_content():
                binary_data += b
            file_name = self.drive.put(
                name=f'{self.user_id}/{event.message.id}.jpeg',
                data=binary_data,
                content_type=data.content_type,
            )
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f'{BASE_PROJECT_URL}/images{file_name.replace(self.user_id, "", 1)}?token={user_token}\nに保存しました'
                )
            )
        else:
            reply = [
                TextSendMessage(text=f'You: {event.message.text}'),
            ]
            image_file_paths = self.drive.list(prefix=self.user_id)["names"]
            if image_file_paths:
                reply.append(
                    TextSendMessage(
                        text="\n\n".join(map(lambda x: f'{BASE_PROJECT_URL}/images{x.replace(self.user_id, "", 1)}?token={user_token}', image_file_paths))
                    )
                )
            else:
                reply.append(
                    TextSendMessage(
                        text="クラウドに保存されている画像はありません。"
                    )
                )

            await self.line_bot_api.reply_message(
                event.reply_token,
                reply,
            )

    async def handle_follow_event(self, event: FollowEvent):
        self.db.put({
            'token': str(uuid4()),
        }, key=self.user_id)

        await self.line_bot_api.reply_message(
            event.reply_token,
            [
                TextSendMessage(text=f'Welcome!'),
            ]
        )
    
    async def handle_postback_event(self, event: PostbackEvent):
        mode = event.postback.data
        print(mode)
        if mode == 'memo':
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text='メモ機能の何を使いますか？',
                    quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=PostbackAction(
                                    label='メモ一覧',
                                    data='memo_list',
                                )
                            ),
                            QuickReplyButton(
                                action=PostbackAction(
                                    label='メモ追加',
                                    data='memo_post',
                                )
                            ),
                            QuickReplyButton(
                                action=PostbackAction(
                                    label='メモ削除',
                                    data='memo_deletion',
                                )
                            ),
                        ]
                    )
                )
            )

    async def handler(self):
        # ベント処理List[Event]
        for event in self.events:
            try:
                assert event.source.user_id == os.environ['MY_LINE_USER_ID'], 'user_idが異なります'
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

            except AssertionError as e:
                print(e)
                print(f'{event.source.user_id}から発信')
                await self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="403 Forbidden\nYou have no authority.")
                )
                break
