import asyncio
import os
from typing import List

from fastapi import BackgroundTasks, Request, WebSocket, responses
from linebot.models.events import Event
from linebot.models.send_messages import TextSendMessage

import handlers
from models import PushContentModel
# __init__.pyの12, 18行目のpathに関して__path__[0] -> /tmpに変更した
from scrape_sites import scrape_atcoder, scrape_lancers, get_text_lancers, get_text_atcoder
from settings import (
    DB_SCRAPE_RESULTS,
    DEBUG,
    DRIVE_LINE_BOT_DRIVE,
    LINE_API,
    LINE_PARSER,
    app,
)


@app.post('/callback/')
async def handle_line_request(request: Request, bg_tasks: BackgroundTasks):
    # 署名検証・イベント取得
    events: List[Event] = LINE_PARSER.parse(
        (await request.body()).decode('utf-8'),
        request.headers['X-Line-Signature']
    )

    bg_tasks.add_task(handlers.handle_events, line_api=LINE_API, events=events, db=DB_SCRAPE_RESULTS, drive=DRIVE_LINE_BOT_DRIVE)

    return 'ok'


@app.get('/notify/')
async def notify(request: Request, bg_tasks: BackgroundTasks):
    messages_list = []
    
    results = await asyncio.gather(
        scrape_atcoder(),
        scrape_lancers(),
    )

    result_atcoder, result_lancers = results

    text_atcoder = get_text_atcoder(result_atcoder, DB_SCRAPE_RESULTS)
    text_lancers = get_text_lancers(result_lancers, DB_SCRAPE_RESULTS)
    
    if text_atcoder is not None:
        messages_list.append(
            TextSendMessage(text=text_atcoder)
        )
    
    if text_lancers is not None:
        messages_list.append(
            TextSendMessage(text=text_lancers)
        )

    await LINE_API.push_message_async(
        os.environ['MY_LINE_USER_ID'],
        messages_list if messages_list else TextSendMessage(text='更新無し'),
    )
    return 'ok'

@app.get('/images/{file_name}/')
async def show_image(file_name: str):
    image = DRIVE_LINE_BOT_DRIVE.get(file_name)
    return responses.StreamingResponse(image.iter_chunks(), media_type='image/png')

@app.post('/push/')
async def push_message(content: PushContentModel):
    if not content.type:
        content.type = '未設定'
    text = f'type:{content.type}\nbody:{content.body}'

    await LINE_API.push_message_async(
        os.environ['MY_LINE_USER_ID'],
        TextSendMessage(text)
    )
    return 'ok'


if not DEBUG:
    from crons import *


