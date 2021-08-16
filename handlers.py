from typing import List

from aiolinebot.api import AioLineBotApi
from linebot.models import TextMessage
from linebot.models.events import Event


async def handle_events(line_api:AioLineBotApi, events:List[Event]):
    # イベント処理List[Event]
    for event in events:
        try:
            await line_api.reply_message_async(
                event.reply_token,
                TextMessage(text=f'You: {event.message.text}')
            )
        except Exception as e:
            print(e)
            print('-' * 60)
