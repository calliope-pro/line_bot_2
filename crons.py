from settings import app, BASE_PROJECT_URL
import requests

@app.lib.cron()
def get_notify(event):
    response = requests.get(f'{BASE_PROJECT_URL}/notify/')
    print(response.status_code)
    return
