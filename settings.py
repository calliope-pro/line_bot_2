import os

from deta import Deta
from aiohttp import ClientSession
from deta import App
from fastapi import FastAPI
from linebot import AsyncLineBotApi, WebhookParser
from linebot.aiohttp_async_http_client import AiohttpAsyncHttpClient


BASE_PROJECT_URL = 'https://calliope-bot.deta.dev'

CHANNEL_SECRET = os.environ['CHANNEL_SECRET']
CHANNEL_ACCESS_TOKEN = os.environ['CHANNEL_ACCESS_TOKEN']

LINE_BOT_API = AsyncLineBotApi(CHANNEL_ACCESS_TOKEN, AiohttpAsyncHttpClient(ClientSession()))
LINE_PARSER = WebhookParser(CHANNEL_SECRET)

app = App(FastAPI())

deta = Deta(os.environ['DETA_PROJECT_KEY'])

DB_SCRAPE_RESULTS = deta.Base('scrape_results')
DRIVE_LINE_BOT_DRIVE = deta.Drive('line-bot-drive')
