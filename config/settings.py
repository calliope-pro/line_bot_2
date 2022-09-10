from datetime import timedelta, timezone
from enum import Enum
import os

from deta import App, Deta
from aiohttp import ClientSession
from fastapi import FastAPI
from linebot import AsyncLineBotApi, WebhookParser
from linebot.aiohttp_async_http_client import AiohttpAsyncHttpClient

app = App(FastAPI())

BASE_PROJECT_URL = 'https://calliope-bot.deta.dev'

CHANNEL_SECRET = os.environ['CHANNEL_SECRET']
CHANNEL_ACCESS_TOKEN = os.environ['CHANNEL_ACCESS_TOKEN']

LINE_BOT_API = AsyncLineBotApi(CHANNEL_ACCESS_TOKEN, AiohttpAsyncHttpClient(ClientSession()))
LINE_PARSER = WebhookParser(CHANNEL_SECRET)

deta = Deta(os.environ['DETA_PROJECT_KEY'])

DB_LINE_ACCOUNTS = deta.Base('line_accounts')
DB_REMINDERS = deta.Base('reminders')
DB_SCRAPE_RESULTS = deta.Base('scrape_results')
DRIVE_LINE_BOT_DRIVE = deta.Drive('line-bot-drive')

IS_MAINTENANCE = bool(int(os.environ['IS_MAINTENANCE']))

JST = timezone(timedelta(hours=9), 'JST')

class PostbackActionData(Enum):
    normal = 'normal'
    memo = 'memo'
    memo_list = 'memo_list'
    memo_post = 'memo_post'
    memo_deletion = 'memo_deletion'
    reminder = 'reminder'
    reminder_list = 'reminder_list'
    reminder_post_datetime = 'reminder_post_datetime'
    reminder_post_content = 'reminder_post_content'
    reminder_deletion = 'reminder_deletion'
    usage = 'usage'
    inquiry = 'inquiry'
    terminate = 'terminate'