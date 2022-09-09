from datetime import datetime

import requests

from settings import JST, app, BASE_PROJECT_URL

@app.lib.cron()
def notify_works(event):
    now = datetime.now(JST).replace(tzinfo=None)
    if now.minute == 0 and now.hour % 4 == 2:
        pass
    response = requests.get(f'{BASE_PROJECT_URL}/notify/')
    print(response.status_code)
    return

@app.lib.cron()
def notify_reminders(event):
    response = requests.get(f'{BASE_PROJECT_URL}/remind/')
    print(response.status_code)
    return
