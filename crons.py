import asyncio
from datetime import datetime
from typing import List

import requests
from linebot.models.send_messages import TextSendMessage
from pydantic import parse_obj_as

from models import ReminderWithKeyModel
from settings import DB_REMINDERS, JST, LINE_BOT_API, app, BASE_PROJECT_URL

@app.lib.cron()
def notify_works(event):
    now = datetime.now(JST).replace(tzinfo=None)
    if now.minute == 0 and now.hour % 4 == 2:
        response = requests.get(f'{BASE_PROJECT_URL}/notify/')
        print(response.status_code)
        return

@app.lib.cron()
def notify_reminders(event):
    response = requests.get(f'{BASE_PROJECT_URL}/remind/')
    print(response.status_code)
    return
