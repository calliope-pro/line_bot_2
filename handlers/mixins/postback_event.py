from datetime import datetime, timedelta
from typing import List

from linebot.models.actions import DatetimePickerAction, PostbackAction
from linebot.models.events import PostbackEvent
from linebot.models.send_messages import QuickReply, QuickReplyButton, TextSendMessage
from pydantic import parse_obj_as

from config.settings import (
    BASE_PROJECT_URL,
    DB_LINE_ACCOUNTS,
    DB_REMINDERS,
    JST,
    PostbackActionData,
)
from models import ReminderModel, ReminderWithKeyModel, UserModel, UserWithKeyModel

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
        now = datetime.now(JST).replace(tzinfo=None)
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
                f'{number}:\n{(datetime.fromisoformat(reminder.datetime) + timedelta(hours=9)).strftime("%Y/%m/%d %H:%M")} {reminder.content}'
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
                            lambda x: f'{BASE_PROJECT_URL}/images{x.replace(self.user_id, "", 1)}?token={user.token}',
                            image_file_paths,
                        )
                    )
                ),
            )
        else:
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="クラウドに保存されている画像はありません。"),
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
                """このcalliope_botは現在大きく3つの機能を有しております。
①写真を投稿することで自動的にクラウドに保存され、保存先がurlとして取得できます。平常時メッセージを送った際には、クラウドに保存されている全ての画像のurlを取得できます。
②メモ一覧, 追加, 削除がリッチメニューを通して操作できます。
③時間を設定しリマインダーを登録することができます。"""
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

    async def _handle_inquiry(self, event: PostbackEvent):
        await self.line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text="作成中です。")
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

        elif data == PostbackActionData.inquiry.value:
            await self._handle_inquiry(event)
