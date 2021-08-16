import asyncio
import os
from typing import List, Union

from aiolinebot import AioLineBotApi
from fastapi import BackgroundTasks, FastAPI, Request
from linebot import WebhookParser
from linebot.models import TextMessage
from linebot.models.events import Event, MessageEvent

from utils.scrape_sites import scrape_atcoder, scrape_lancers
import handlers

CHANNEL_SECRET = os.environ['CHANNEL_SECRET']
CHANNEL_ACCESS_TOKEN = os.environ['CHANNEL_ACCESS_TOKEN']

line_api = AioLineBotApi(CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(CHANNEL_SECRET)

app = FastAPI()


@app.post('/callback/')
async def handle_request(request: Request, bg_tasks: BackgroundTasks):
    # 署名検証・イベント取得
    events:List[Event] = parser.parse(
        (await request.body()).decode('utf-8'),
        request.headers['X-Line-Signature']
    )

    bg_tasks.add_task(handlers.handle_events, line_api=line_api, events=events)

    return 'ok'



@app.get('/')
async def notify(request: Request, bg_tasks=BackgroundTasks):
    try:
        response = await asyncio.gather(scrape_atcoder.scrape(), scrape_lancers.scrape())
        result_atcoder, result_lancers = response
        info_atcoder = result_atcoder[0] + '\n' + '\n' + result_atcoder[1]
        info_lancers = '\n\n--------------------------------\n\n'.join(map(lambda x: '\n・'.join(x), result_lancers))
        await line_api.push_message_async(os.environ['MY_LINE_USER_ID'], [TextMessage(text=info_atcoder), TextMessage(text=info_lancers)])
    except Exception as e:
        print(e)
        print('-' * 60)

    return 'ok'

