import mimetypes
import os
from datetime import timedelta, timezone
from enum import Enum
from pathlib import Path

from aiohttp import ClientSession
from deta import Deta
from fastapi import FastAPI
from linebot import AsyncLineBotApi, WebhookParser
from linebot.aiohttp_async_http_client import AiohttpAsyncHttpClient

try:
    from deta import App

    app = App(FastAPI())
except ImportError:
    print("Development mode...")

PROJECT_DIR = Path().resolve().parent.parent

BASE_PROJECT_URL = "https://vz88mi.deta.dev"

CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]
CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]

LINE_BOT_API = AsyncLineBotApi(
    CHANNEL_ACCESS_TOKEN, AiohttpAsyncHttpClient(ClientSession())
)
LINE_PARSER = WebhookParser(CHANNEL_SECRET)

deta = Deta(os.environ["DETA_PROJECT_KEY"])

DB_LINE_ACCOUNTS = deta.Base("line_accounts")
DB_REMINDERS = deta.Base("reminders")
DB_SCRAPE_RESULTS = deta.Base("scrape_results")
DRIVE_LINE_BOT_DRIVE = deta.Drive("line-bot-drive")

IS_MAINTENANCE = bool(int(os.environ["IS_MAINTENANCE"]))

JST = timezone(timedelta(hours=9), "JST")

mimetypes.add_type("audio/x-m4a", ".m4a")
mimetypes.add_type("audio/mpeg", ".mp3")


class PostbackActionData(Enum):
    normal = "normal"
    memo = "memo"
    memo_list = "memo_list"
    memo_post = "memo_post"
    memo_deletion = "memo_deletion"
    reminder = "reminder"
    reminder_list = "reminder_list"
    reminder_post_datetime = "reminder_post_datetime"
    reminder_post_content = "reminder_post_content"
    reminder_deletion = "reminder_deletion"
    file = "file"
    file_storage_capacity = "file_storage_capacity"
    file_list = "file_list"
    file_post = "file_post"
    file_deletion = "file_deletion"
    oracle = "oracle"
    sensoji_oracle = "sensoji_oracle"
    fushimi_oracle = "fushimi_oracle"
    usage = "usage"
    terminate = "terminate"
