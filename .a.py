import os
from linebot.models.actions import MessageAction, DatetimePickerAction, PostbackAction
from linebot.models.rich_menu import RichMenu, RichMenuSize, RichMenuArea, RichMenuBounds
from linebot import LineBotApi

BASE_PROJECT_URL = 'https://calliope-bot.deta.dev'

CHANNEL_SECRET = os.environ['CHANNEL_SECRET']
CHANNEL_ACCESS_TOKEN = os.environ['CHANNEL_ACCESS_TOKEN']

LINE_BOT_API = LineBotApi(CHANNEL_ACCESS_TOKEN)

raw_rich_menu = RichMenu(
    size=RichMenuSize(width=2500, height=1686),
    selected=True,
    name='Main, 4divs, basic function',
    chat_bar_text='See more!',
    areas=[
        RichMenuArea(
            bounds=RichMenuBounds(
                x=250,
                y=168,
                width=750,
                height=508,
            ),
            action=MessageAction(
                label='usage',
                text='''このcalliope_botは現在大きく3つの機能を有しております。
①写真を投稿することで自動的にクラウドに保存され、保存先がurlとして取得できます。平常時メッセージを送った際には、クラウドに保存されている全ての画像のurlを取得できます。
②メモ一覧, 追加, 削除がリッチメニューを通して操作できます。(作成中)
③時間を設定しリマインダーを登録することができます。(作成中)
'''
            )
        ),
        RichMenuArea(
            bounds=RichMenuBounds(
                x=1500,
                y=168,
                width=750,
                height=508,
            ),
            action=PostbackAction(
                label='handle memo',
                data='memo',
            )
        ),
        RichMenuArea(
            bounds=RichMenuBounds(
                x=250,
                y=1011,
                width=750,
                height=508,
            ),
            action=DatetimePickerAction(
                label='set reminder time',
                data='reminder',
                mode='datetime',
            )
        ),
        RichMenuArea(
            bounds=RichMenuBounds(
                x=1500,
                y=1011,
                width=750,
                height=508,
            ),
            action=MessageAction(
                label='inquiry',
                text='お問い合わせ'
            )
        ),
    ]
)

rich_menu_id = LINE_BOT_API.create_rich_menu(raw_rich_menu)

with open('LINE_rich_menu_design_template/richmenu_1662508136482.jpg', 'rb') as f:
    LINE_BOT_API.set_rich_menu_image(rich_menu_id, 'image/png', f)

LINE_BOT_API.set_default_rich_menu(rich_menu_id)
