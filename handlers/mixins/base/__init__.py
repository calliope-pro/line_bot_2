from deta import _Drive
from linebot import AsyncLineBotApi

class EventHandlerMixinBase:
    line_bot_api: AsyncLineBotApi
    drive: _Drive
    user_id: str
