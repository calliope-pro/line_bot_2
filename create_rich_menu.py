import os

from linebot import LineBotApi
from linebot.models.actions import PostbackAction, URIAction
from linebot.models.rich_menu import (
    RichMenu,
    RichMenuArea,
    RichMenuBounds,
    RichMenuSize,
)
from linebot.models.send_messages import TextSendMessage

from config.settings import PostbackActionData

BASE_PROJECT_URL = "https://calliope-bot.deta.dev"

CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]
CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]

LINE_BOT_API = LineBotApi(CHANNEL_ACCESS_TOKEN)

rich_menu_width = 2500
rich_menu_height = 1686

raw_rich_menu = RichMenu(
    size=RichMenuSize(width=2500, height=1686),
    selected=True,
    name="Main, 6divs, basic function",
    chat_bar_text="See more!",
    areas=[
        RichMenuArea(
            bounds=RichMenuBounds(
                x=rich_menu_width * 1 / 30,
                y=0,
                width=rich_menu_width * 8 / 30,
                height=rich_menu_height * 1 / 2,
            ),
            action=PostbackAction(
                label="handle memos",
                data=PostbackActionData.memo.value,
            ),
        ),
        RichMenuArea(
            bounds=RichMenuBounds(
                x=rich_menu_width * 11 / 30,
                y=0,
                width=rich_menu_width * 8 / 30,
                height=rich_menu_height * 1 / 2,
            ),
            action=PostbackAction(
                label="handle reminders",
                data=PostbackActionData.reminder.value,
            ),
        ),
        RichMenuArea(
            bounds=RichMenuBounds(
                x=rich_menu_width * 21 / 30,
                y=0,
                width=rich_menu_width * 8 / 30,
                height=rich_menu_height * 1 / 2,
            ),
            action=PostbackAction(
                label="handle files",
                data=PostbackActionData.file.value,
            ),
        ),
        RichMenuArea(
            bounds=RichMenuBounds(
                x=rich_menu_width * 1 / 30,
                y=rich_menu_height * 1 / 2,
                width=rich_menu_width * 8 / 30,
                height=rich_menu_height * 1 / 2,
            ),
            action=PostbackAction(
                label="usage",
                data=PostbackActionData.usage.value,
            ),
        ),
        RichMenuArea(
            bounds=RichMenuBounds(
                x=rich_menu_width * 11 / 30,
                y=rich_menu_height * 1 / 2,
                width=rich_menu_width * 8 / 30,
                height=rich_menu_height * 1 / 2,
            ),
            action=URIAction(
                label="blog",
                uri="https://cacaca-blog.vercel.app",
            ),
        ),
        RichMenuArea(
            bounds=RichMenuBounds(
                x=rich_menu_width * 21 / 30,
                y=rich_menu_height * 1 / 2,
                width=rich_menu_width * 8 / 30,
                height=rich_menu_height * 1 / 2,
            ),
            action=PostbackAction(
                label="inquiry",
                data=PostbackActionData.inquiry.value,
            ),
        ),
    ],
)

rich_menu_id = LINE_BOT_API.create_rich_menu(raw_rich_menu)

with open("rich_menu_imgs/richmenu.jpg", "rb") as f:
    LINE_BOT_API.set_rich_menu_image(rich_menu_id, "image/png", f)

LINE_BOT_API.set_default_rich_menu(rich_menu_id)

LINE_BOT_API.push_message(
    os.environ["MY_LINE_USER_ID"],
    TextSendMessage(f"richmenu id:{rich_menu_id}\n設定されました"),
)

print("fin.")
