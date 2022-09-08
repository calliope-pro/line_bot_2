import asyncio
from datetime import datetime
from typing import List

import requests
from linebot.models.send_messages import TextSendMessage
from pydantic import parse_obj_as

from models import ReminderWithKeyModel
from settings import DB_REMINDERS, JST, LINE_BOT_API, app, BASE_PROJECT_URL

@app.lib.cron()
def get_notify(event):
    now = datetime.now(JST).replace(tzinfo=None)
    if now.minute == 0 and now.hour % 4 == 2:
        response = requests.get(f'{BASE_PROJECT_URL}/notify/')
        print(response.status_code)
        return

@app.lib.cron()
async def notify_reminders(event):
    reminders_raw = DB_REMINDERS.fetch().items
    reminders = parse_obj_as(List[ReminderWithKeyModel], reminders_raw)
    now = datetime.utcnow().isoformat(timespec='minutes')

    coroutines = []
    for reminder in reminders:
        if reminder.datetime == now:
            coroutines.append(
                LINE_BOT_API.push_message(
                    reminder.line_user_id,
                    TextSendMessage(reminder.content)
                )
            )
    await asyncio.gather(*coroutines)
