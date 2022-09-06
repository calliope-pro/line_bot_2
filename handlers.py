import os
from typing import List

from deta import _Base, _Drive
from linebot import AsyncLineBotApi
from linebot.models.events import Event, MessageEvent, FollowEvent
from linebot.models.send_messages import TextSendMessage

from settings import BASE_PROJECT_URL

class EventsHandler:
    def __init__(self, line_bot_api: AsyncLineBotApi, events: List[Event], db: _Base, drive: _Drive):
        self.line_bot_api = line_bot_api
        self.events = events
        self.db = db
        self.drive = drive

    async def handle_message_event(self, event: MessageEvent):
        print(event.message.type)
        if event.message.type == 'image':
            data = await self.line_bot_api.get_message_content(event.message.id)
            print(data)
            print(data.content_type)
            binary_data = b''
            for b in data.iter_content():
                binary_data += b
            await data.response.close()
            file_name = self.drive.put(
                name=f'{event.message.id}.jpeg',
                data=binary_data,
                content_type=data.content_type,
            )
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f'{BASE_PROJECT_URL}/images/{file_name}\nに保存しました')
            )
        else:
            await self.line_bot_api.reply_message(
                event.reply_token,
                [
                    # ImageSendMessage(
                    #     f'{BASE_PROJECT_URL}/images/14734080206120.png/',
                    #     f'https://media.istockphoto.com/vectors/thumbnail-image-vector-graphic-vector-id1147544807?k=20&m=1147544807&s=612x612&w=0&h=pBhz1dkwsCMq37Udtp9sfxbjaMl27JUapoyYpQm0anc=',
                    # ),
                    TextSendMessage(text=f'You: {event.message.text}'),
                    TextSendMessage(text="\n".join(map(lambda x: f'{BASE_PROJECT_URL}/images/{x}', self.drive.list()["names"]))),
                ]
            )

    async def handle_follow_event(self, event: FollowEvent):
        pass

    async def handler(self):
        # ベント処理List[Event]
        for event in self.events:
            try:
                assert event.source.user_id == os.environ['MY_LINE_USER_ID'], 'user_idが異なります'

                # メッセージイベント
                if isinstance(event, MessageEvent):
                    await self.handle_message_event(event)
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
