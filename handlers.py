import os
from typing import List

from deta import _Base, _Drive
from linebot.models.events import Event
from linebot.models.send_messages import ImageSendMessage, TextSendMessage

from aiolinebot import AioLineBotApi
from settings import BASE_PROJECT_URL


async def handle_events(line_api: AioLineBotApi, events: List[Event], db: _Base, drive: _Drive):
    # イベント処理List[Event]
    for event in events:
        try:
            assert event.source.user_id == os.environ['MY_LINE_USER_ID'], 'user_idが異なります'
            
            if event.message.type == 'image':
                data = await line_api.get_message_content_async(event.message.id)
                binary_data = b''
                async for b in data.iter_content():
                    binary_data += b
                await data.response.close()
                file_name = drive.put(
                    name=f'{event.message.id}.png',
                    data=binary_data,
                    content_type=data.content_type,
                )
                await line_api.reply_message_async(
                    event.reply_token,
                    TextSendMessage(text=f'{BASE_PROJECT_URL}/images/{file_name}\nに保存しました')
                )

            else:
                await line_api.reply_message_async(
                    event.reply_token,
                    [
                        # ImageSendMessage(
                        #     f'{BASE_PROJECT_URL}/images/14734080206120.png/',
                        #     f'https://media.istockphoto.com/vectors/thumbnail-image-vector-graphic-vector-id1147544807?k=20&m=1147544807&s=612x612&w=0&h=pBhz1dkwsCMq37Udtp9sfxbjaMl27JUapoyYpQm0anc=',
                        # ),
                        TextSendMessage(text=f'You sended: {event.message.text}'),
                        TextSendMessage(text="\n".join(map(lambda x: f'{BASE_PROJECT_URL}/images/{x}', drive.list()["names"]))),
                    ]
                )

        except AssertionError as e:
            print(e)
            print(f'{event.source.user_id}から発信')
            await line_api.reply_message_async(
                event.reply_token,
                TextSendMessage(text="403 Forbidden\nYou have no authority.")
            )

        # except Exception as e:
        #     print(e)
        #     print('-' * 60)
