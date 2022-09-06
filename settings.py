import os

from deta import Deta
from fastapi import FastAPI
from linebot import WebhookParser

from aiolinebot import AioLineBotApi

DEBUG = False

BASE_PROJECT_URL = 'https://calliope-bot.deta.dev'

CHANNEL_SECRET = os.environ['CHANNEL_SECRET']
CHANNEL_ACCESS_TOKEN = os.environ['CHANNEL_ACCESS_TOKEN']

LINE_API = AioLineBotApi(CHANNEL_ACCESS_TOKEN)
LINE_PARSER = WebhookParser(CHANNEL_SECRET)

try:
    from local_settings import DEBUG
    app = FastAPI(debug=DEBUG)
except ImportError:
    from deta import App
    app = App(FastAPI())

deta = Deta(os.environ['DETA_PROJECT_KEY'])

DB_SCRAPE_RESULTS = deta.Base('scrape_results')
DRIVE_LINE_BOT_DRIVE = deta.Drive('line-bot-drive')
