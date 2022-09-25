import random
from datetime import datetime, timedelta
from typing import List

from linebot.models.actions import DatetimePickerAction, PostbackAction
from linebot.models.events import PostbackEvent
from linebot.models.send_messages import QuickReply, QuickReplyButton, TextSendMessage
from linebot.models.template import (
    ImageCarouselColumn,
    ImageCarouselTemplate,
    TemplateSendMessage,
)
from pydantic import parse_obj_as

from config.settings import (
    BASE_PROJECT_URL,
    DB_LINE_ACCOUNTS,
    DB_REMINDERS,
    PostbackActionData,
)
from models import ReminderModel, ReminderWithKeyModel, UserModel, UserWithKeyModel
from utils.time import get_jst_from_utc_isoformat, get_jst_now

from .base import EventHandlerMixinBase


class PostbackEventHandlerMixin(EventHandlerMixinBase):
    async def _handle_memo(self, event: PostbackEvent):
        quick_reply = QuickReply(
            items=[
                QuickReplyButton(
                    action=PostbackAction(
                        label="メモ一覧",
                        data=PostbackActionData.memo_list.value,
                    )
                ),
                QuickReplyButton(
                    action=PostbackAction(
                        label="メモ追加",
                        data=PostbackActionData.memo_post.value,
                    )
                ),
                QuickReplyButton(
                    action=PostbackAction(
                        label="メモ削除",
                        data=PostbackActionData.memo_deletion.value,
                    )
                ),
            ]
        )
        await self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="メモ機能の何を使いますか？",
                quick_reply=quick_reply,
            ),
        )

    async def _handle_memo_list(self, event: PostbackEvent):
        user = UserWithKeyModel.parse_obj(DB_LINE_ACCOUNTS.get(self.user_id))
        if user.memos:
            memo_list_text = "現在クラウドに保存されているメモは↓\n"
            memo_list_text += "\n".join(
                f"{number}: {value}" for number, value in enumerate(user.memos, 1)
            )
        else:
            memo_list_text = "クラウドに保存されているメモはありません。"
        await self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=memo_list_text,
            ),
        )

    async def _handle_memo_post(self, event: PostbackEvent):
        DB_LINE_ACCOUNTS.update(
            UserModel.construct(mode=PostbackActionData.memo_post.value).dict(),
            key=self.user_id,
        )
        quick_reply = QuickReply(
            items=[
                QuickReplyButton(
                    action=PostbackAction(
                        label="メモ追加を終了する",
                        data=PostbackActionData.terminate.value,
                    )
                ),
            ]
        )
        await self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="メモしたいことを入力してください。\n\n終了したい場合は以下のボタンを押してください。",
                quick_reply=quick_reply,
            ),
        )

    async def _handle_memo_deletion(self, event: PostbackEvent):
        DB_LINE_ACCOUNTS.update(
            UserModel.construct(mode=PostbackActionData.memo_deletion.value).dict(),
            key=self.user_id,
        )
        quick_reply = QuickReply(
            items=[
                QuickReplyButton(
                    action=PostbackAction(
                        label="メモ削除を終了する",
                        data=PostbackActionData.terminate.value,
                    )
                ),
            ]
        )
        await self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="削除したいメモの番号を入力してください。\n\n終了したい場合は以下のボタンを押してください。",
                quick_reply=quick_reply,
            ),
        )

    async def _handle_reminder(self, event: PostbackEvent):
        now = get_jst_now()
        quick_reply = QuickReply(
            items=[
                QuickReplyButton(
                    action=PostbackAction(
                        label="リマインダー一覧",
                        data=PostbackActionData.reminder_list.value,
                    )
                ),
                QuickReplyButton(
                    action=DatetimePickerAction(
                        label="リマインダー追加",
                        data=PostbackActionData.reminder_post_content.value,
                        mode="datetime",
                        initial=(now + timedelta(minutes=1)).isoformat(
                            timespec="minutes"
                        ),
                        max=(now + timedelta(days=30)).isoformat(timespec="minutes"),
                        min=(now + timedelta(minutes=1)).isoformat(timespec="minutes"),
                    )
                ),
                QuickReplyButton(
                    action=PostbackAction(
                        label="リマインダー削除",
                        data=PostbackActionData.reminder_deletion.value,
                    )
                ),
            ]
        )
        await self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="リマインダー機能の何を使いますか？",
                quick_reply=quick_reply,
            ),
        )

    async def _handle_reminder_list(self, event: PostbackEvent):
        user_reminders_raw = DB_REMINDERS.fetch({"line_user_id": self.user_id}).items
        user_reminders = parse_obj_as(List[ReminderWithKeyModel], user_reminders_raw)
        if user_reminders:
            reminder_list_text = "現在クラウドに保存されているリマインダーは↓\n"
            reminder_list_text += "\n".join(
                f'{number}:\n{(get_jst_from_utc_isoformat(reminder.datetime)).strftime("%Y/%m/%d %H:%M")} {reminder.content}'
                for number, reminder in enumerate(user_reminders, 1)
            )
        else:
            reminder_list_text = "クラウドに保存されているリマインダーはありません。"
        await self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=reminder_list_text,
            ),
        )

    async def _handle_reminder_post_content(self, event: PostbackEvent):
        DB_REMINDERS.put(
            ReminderModel(
                datetime=(
                    datetime.fromisoformat(event.postback.params["datetime"])
                    - timedelta(hours=9)
                ).isoformat(timespec="minutes"),
                content="",
                line_user_id=self.user_id,
            ).dict(),
            expire_at=datetime.fromisoformat(event.postback.params["datetime"])
            - timedelta(hours=8, minutes=59),
            key=str(datetime.now().timestamp()),
        )
        DB_LINE_ACCOUNTS.update(
            UserModel.construct(
                mode=PostbackActionData.reminder_post_content.value
            ).dict(),
            key=self.user_id,
        )
        await self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="リマインドしたいことを入力してください。",
            ),
        )

    async def _handle_reminder_deletion(self, event: PostbackEvent):
        DB_LINE_ACCOUNTS.update(
            UserModel.construct(mode=PostbackActionData.reminder_deletion.value).dict(),
            key=self.user_id,
        )
        quick_reply = QuickReply(
            items=[
                QuickReplyButton(
                    action=PostbackAction(
                        label="リマインダー削除を終了する",
                        data=PostbackActionData.terminate.value,
                    )
                ),
            ]
        )
        await self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="削除したいリマインダーの番号を入力してください。\n\n終了したい場合は以下のボタンを押してください。",
                quick_reply=quick_reply,
            ),
        )

    async def _handle_file(self, event: PostbackEvent):
        quick_reply = QuickReply(
            items=[
                QuickReplyButton(
                    action=PostbackAction(
                        label="ファイル一覧",
                        data=PostbackActionData.file_list.value,
                    )
                ),
                QuickReplyButton(
                    action=PostbackAction(
                        label="ファイル追加",
                        data=PostbackActionData.file_post.value,
                    )
                ),
                QuickReplyButton(
                    action=PostbackAction(
                        label="ファイル削除",
                        data=PostbackActionData.file_deletion.value,
                    )
                ),
            ]
        )
        await self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="ファイル機能の何を使いますか？",
                quick_reply=quick_reply,
            ),
        )

    async def _handle_file_list(self, event: PostbackEvent):
        user = UserWithKeyModel.parse_obj(DB_LINE_ACCOUNTS.get(self.user_id))
        image_file_paths: List[str] = self.drive.list(prefix=self.user_id)["names"]
        if image_file_paths:
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="\n\n".join(
                        map(
                            lambda x: f'{BASE_PROJECT_URL}/storage{x.replace(self.user_id, "", 1)}?token={user.token}',
                            image_file_paths,
                        )
                    )
                ),
            )
        else:
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="クラウドに保存されているファイルはありません。"),
            )

    async def _handle_file_post(self, event: PostbackEvent):
        DB_LINE_ACCOUNTS.update(
            UserModel.construct(mode=PostbackActionData.file_post.value).dict(),
            key=self.user_id,
        )
        quick_reply = QuickReply(
            items=[
                QuickReplyButton(
                    action=PostbackAction(
                        label="ファイル追加を終了する",
                        data=PostbackActionData.terminate.value,
                    )
                ),
            ]
        )
        await self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="保存したいファイルを送信してください。\n\n終了したい場合は以下のボタンを押してください。",
                quick_reply=quick_reply,
            ),
        )

    async def _handle_file_deletion(self, event: PostbackEvent):
        DB_LINE_ACCOUNTS.update(
            UserModel.construct(mode=PostbackActionData.file_deletion.value).dict(),
            key=self.user_id,
        )
        quick_reply = QuickReply(
            items=[
                QuickReplyButton(
                    action=PostbackAction(
                        label="ファイル削除を終了する",
                        data=PostbackActionData.terminate.value,
                    )
                ),
            ]
        )
        await self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="削除したいファイルのURLを入力してください。\n\n終了したい場合は以下のボタンを押してください。",
                quick_reply=quick_reply,
            ),
        )

    async def _handle_usage(self, event: PostbackEvent):
        await self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                """このcalliope_botは現在大きく3つの機能を有しています。
基本的に画面下部のリッチメニューを操作することで用いることが出来ます。
①メモ機能
メモの一覧、追加、削除が出来ます。手短なメモ帳として使うことが出来ます。
②リマインダー機能
リマインダーの一覧、追加,、削除が出来ます。日時を設定してからリマインドしたいことを入力することで、設定された日時にメッセージが送信されます。
通知済みのリマインダーは通知の1分後に自動的に削除されます。
③ファイル機能
ファイルの一覧、追加、削除が出来ます。合計50MBまでクラウドに保存されます。保存されたファイルはURLとして返ってくるためURLを通してファイルを見たり、ダウンロードできたりします。
※フォーマットや端末環境により、URL先で閲覧出来ない可能性があります。
・その他
日替わりおみくじ機能(くじの割合は浅草寺と同じにしています)
運営している中の人のブログへ直接飛べるメニューがあります。

今後実装予定機能
- リマインダーの連続追加機能
- クイックリプライのUX向上
- 何機能を使用中であるかを確認できる機能
- (AIを使用した言語処理)

------
連絡先
calliope_bot
https://line.me/R/ti/p/@574rllla
calliope(運営)
https://line.me/R/ti/p/YzZxFFHMI6"""
            ),
        )

    async def _handle_terminate(self, event: PostbackEvent):
        DB_LINE_ACCOUNTS.update(
            UserModel.construct(mode=PostbackActionData.normal.value).dict(),
            key=self.user_id,
        )
        await self.line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text="終了しました。")
        )

    async def _handle_oracle(self, event: PostbackEvent):
        await self.line_bot_api.reply_message(
            event.reply_token,
            [
                TextSendMessage(text="どの吉凶配分で引きますか"),
                TemplateSendMessage(
                    alt_text="Choose lottery pattern",
                    template=ImageCarouselTemplate(
                        [
                            ImageCarouselColumn(
                                image_url="https://media.istockphoto.com/photos/sensoji-temple-in-tokyo-japan-tokyo-japan-january-22-2019sensoji-at-picture-id1139651438?k=20&m=1139651438&s=612x612&w=0&h=UVzDniEQawMesuHOvsYnn0RSgZNHQVL9SDZjBgLh5cY=",
                                action=PostbackAction(
                                    label="浅草寺",
                                    data=PostbackActionData.sensoji_oracle.value,
                                ),
                            ),
                            ImageCarouselColumn(
                                image_url="https://media.istockphoto.com/photos/torii-gates-in-fushimi-inari-shrine-kyoto-japan-picture-id491222300?k=20&m=491222300&s=612x612&w=0&h=ZU3yWv_26vyDqfQCinhu7AwWrROFP7BqyZfbgyK2R2E=",
                                action=PostbackAction(
                                    label="伏見稲荷大社",
                                    data=PostbackActionData.fushimi_oracle.value,
                                ),
                            ),
                        ]
                    ),
                ),
            ],
        )

    async def _handle_sensoji_oracle(self, event: PostbackEvent):
        today = get_jst_now().date().isoformat()
        lotteries = {
            "大吉": 17,
            "吉": 35,
            "半吉": 5,
            "小吉": 4,
            "末小吉": 3,
            "末吉": 6,
            "凶": 30,
        }
        random.seed(f"{today}-{self.user_id}")
        chosen_lottery = random.choices(
            tuple(lotteries.keys()), weights=tuple(lotteries.values())
        )[0]
        await self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"本日の運勢は{chosen_lottery}です。"),
        )

    async def _handle_fushimi_oracle(self, event: PostbackEvent):
        today = get_jst_now().date().isoformat()
        lotteries = {
            "大大吉": 2,
            "大吉": 6,
            "凶後大吉": 1,
            "凶後吉": 4,
            "末大吉": 3,
            "末吉": 3,
            "向大吉": 2,
            "吉": 2,
            "中吉": 1,
            "小吉": 1,
            "小凶後吉": 1,
            "後吉": 1,
            "吉凶未分末大吉": 1,
            "吉凶不分末吉": 1,
            "吉凶相半": 1,
            "吉凶相交末吉": 1,
            "吉凶相央": 1,
        }
        random.seed(f"{today}-{self.user_id}")
        chosen_lottery = random.choices(
            tuple(lotteries.keys()), weights=tuple(lotteries.values())
        )[0]
        await self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"本日の運勢は{chosen_lottery}です。"),
        )

    async def handle_postback_event(self, event: PostbackEvent):
        data = event.postback.data
        if data == PostbackActionData.memo.value:
            await self._handle_memo(event)

        elif data == PostbackActionData.memo_list.value:
            await self._handle_memo_list(event)

        elif data == PostbackActionData.memo_post.value:
            await self._handle_memo_post(event)

        elif data == PostbackActionData.memo_deletion.value:
            await self._handle_memo_deletion(event)

        elif data == PostbackActionData.reminder.value:
            await self._handle_reminder(event)

        elif data == PostbackActionData.reminder_list.value:
            await self._handle_reminder_list(event)

        elif data == PostbackActionData.reminder_post_content.value:
            await self._handle_reminder_post_content(event)

        elif data == PostbackActionData.reminder_deletion.value:
            await self._handle_reminder_deletion(event)

        elif data == PostbackActionData.file.value:
            await self._handle_file(event)

        elif data == PostbackActionData.file_list.value:
            await self._handle_file_list(event)

        elif data == PostbackActionData.file_post.value:
            await self._handle_file_post(event)

        elif data == PostbackActionData.file_deletion.value:
            await self._handle_file_deletion(event)

        elif data == PostbackActionData.usage.value:
            await self._handle_usage(event)

        elif data == PostbackActionData.terminate.value:
            await self._handle_terminate(event)

        elif data == PostbackActionData.oracle.value:
            await self._handle_oracle(event)

        elif data == PostbackActionData.sensoji_oracle.value:
            await self._handle_sensoji_oracle(event)

        elif data == PostbackActionData.fushimi_oracle.value:
            await self._handle_fushimi_oracle(event)
