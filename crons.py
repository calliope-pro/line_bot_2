from datetime import datetime

import requests

from config.settings import BASE_PROJECT_URL, JST, app


@app.post("/__space/v0/actions")
def notify_reminders():
    try:
        requests.get(f"{BASE_PROJECT_URL}/remind/")
    except Exception as e:
        print(e)

    try:
        now = datetime.now(JST).replace(tzinfo=None)
        if now.minute == 0 and now.hour % 4 == 2:
            requests.get(f"{BASE_PROJECT_URL}/notify/")
    except Exception as e:
        print(e)
