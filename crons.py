from datetime import datetime

import requests

from settings import JST, app, BASE_PROJECT_URL

@app.lib.cron()
def notify_reminders(event):
    try:
        requests.get(f'{BASE_PROJECT_URL}/remind/')
    except Exception as e:
        print(e)

    try:
        now = datetime.now(JST).replace(tzinfo=None)
        if now.minute == 0 and now.hour % 4 == 2:
            requests.get(f'{BASE_PROJECT_URL}/notify/')
    except Exception as e:
        print(e)
