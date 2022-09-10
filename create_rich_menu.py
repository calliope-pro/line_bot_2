import os

from linebot import LineBotApi
from linebot.models.actions import PostbackAction
from linebot.models.rich_menu import (
    RichMenu,
    RichMenuArea,
    RichMenuBounds,
    RichMenuSize,
)

from config.settings import PostbackActionData

BASE_PROJECT_URL = "https://calliope-bot.deta.dev"

CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]
CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]

LINE_BOT_API = LineBotApi(CHANNEL_ACCESS_TOKEN)

raw_rich_menu = RichMenu(
    size=RichMenuSize(width=2500, height=1686),
    selected=True,
    name="Main, 4divs, basic function",
    chat_bar_text="See more!",
    areas=[
        RichMenuArea(
            bounds=RichMenuBounds(
                x=250,
                y=168,
                width=750,
                height=508,
            ),
            action=PostbackAction(
                label="usage",
                data=PostbackActionData.usage.value,
            ),
        ),
        RichMenuArea(
            bounds=RichMenuBounds(
                x=1500,
                y=168,
                width=750,
                height=508,
            ),
            action=PostbackAction(
                label="handle memos",
                data=PostbackActionData.memo.value,
            ),
        ),
        RichMenuArea(
            bounds=RichMenuBounds(
                x=250,
                y=1011,
                width=750,
                height=508,
            ),
            action=PostbackAction(
                label="handle reminders",
                data=PostbackActionData.reminder.value,
            ),
        ),
        RichMenuArea(
            bounds=RichMenuBounds(
                x=1500,
                y=1011,
                width=750,
                height=508,
            ),
            action=PostbackAction(
                label="inquiry",
                data=PostbackActionData.inquiry.value,
            ),
        ),
    ],
)

rich_menu_id = LINE_BOT_API.create_rich_menu(raw_rich_menu)

with open("rich_menu_img/richmenu.jpg", "rb") as f:
    LINE_BOT_API.set_rich_menu_image(rich_menu_id, "image/png", f)

LINE_BOT_API.set_default_rich_menu(rich_menu_id)

print("fin.")
