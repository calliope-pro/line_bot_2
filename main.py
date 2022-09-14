import asyncio
import mimetypes
import os
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import BackgroundTasks, HTTPException, Request, responses
from linebot.exceptions import InvalidSignatureError
from linebot.models.events import Event
from linebot.models.send_messages import TextSendMessage
from pydantic import parse_obj_as

from config.settings import (
    DB_LINE_ACCOUNTS,
    DB_REMINDERS,
    DB_SCRAPE_RESULTS,
    DRIVE_LINE_BOT_DRIVE,
    LINE_BOT_API,
    LINE_PARSER,
    app,
)
from handlers import EventsHandler
from models import PushContentModel, ReminderWithKeyModel, UserWithKeyModel
from scrape_sites import (
    get_text_atcoder,
    get_text_lancers,
    scrape_atcoder,
    scrape_lancers,
)


@app.post("/callback/")
async def handle_line_request(request: Request, bg_tasks: BackgroundTasks):
    try:
        # 署名検証・イベント取得
        events: List[Event] = LINE_PARSER.parse(
            (await request.body()).decode("utf-8"), request.headers["X-Line-Signature"]
        )
    except InvalidSignatureError:
        return HTTPException(400, "Invalid signature.")

    event_handler = EventsHandler(LINE_BOT_API, events, DRIVE_LINE_BOT_DRIVE)
    bg_tasks.add_task(event_handler.handle)

    return "ok"


@app.get("/notify/")
async def notify_works(request: Request, bg_tasks: BackgroundTasks):
    messages_list = []

    results = await asyncio.gather(
        scrape_atcoder(),
        scrape_lancers(),
    )

    result_atcoder, result_lancers = results

    text_atcoder = get_text_atcoder(result_atcoder, DB_SCRAPE_RESULTS)
    text_lancers = get_text_lancers(result_lancers, DB_SCRAPE_RESULTS)

    if text_atcoder is not None:
        messages_list.append(TextSendMessage(text=text_atcoder))

    if text_lancers is not None:
        messages_list.append(TextSendMessage(text=text_lancers))

    await LINE_BOT_API.push_message(
        os.environ["MY_LINE_USER_ID"],
        messages_list if messages_list else TextSendMessage(text="更新無し"),
    )
    return "OK"


@app.get("/remind/")
async def notify_reminders():
    now = datetime.utcnow().isoformat(timespec="minutes")
    reminders_raw = DB_REMINDERS.fetch({"datetime": now}).items
    reminders = parse_obj_as(List[ReminderWithKeyModel], reminders_raw)

    coroutines = [
        asyncio.create_task(
            LINE_BOT_API.push_message(
                reminder.line_user_id, TextSendMessage(reminder.content)
            )
        )
        for reminder in reminders
    ]
    await asyncio.gather(*coroutines)
    return "OK"


@app.get("/storage/{file_name}")
def show_file(file_name: str, token: str):
    user = UserWithKeyModel.parse_obj(DB_LINE_ACCOUNTS.fetch({"token": token}).items[0])
    file = DRIVE_LINE_BOT_DRIVE.get(f"{user.key}/{file_name}")
    tmp_path = Path('tmp').resolve().parent / user.key
    try:
        if not tmp_path.exists():
            tmp_path.mkdir(exist_ok=True)
        with (tmp_path / file_name).open("wb") as f:
            for chunk in file.iter_chunks(4096):
                f.write(chunk)
            file.close()
        media_type = mimetypes.guess_type(file_name)[0]
        return responses.FileResponse(str(tmp_path / file_name), media_type=media_type)
    except Exception as e:
        print(e)


@app.post("/push/")
async def push_message(content: PushContentModel):
    if not content.type:
        content.type = "未設定"
    text = f"type:{content.type}\nbody:{content.body}"

    await LINE_BOT_API.push_message(
        os.environ["MY_LINE_USER_ID"], TextSendMessage(text)
    )
    return "ok"


from crons import *
