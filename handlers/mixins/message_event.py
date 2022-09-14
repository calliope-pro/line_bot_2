from datetime import datetime, timedelta
from typing import List

from linebot.models.actions import PostbackAction
from linebot.models.events import MessageEvent
from linebot.models.send_messages import QuickReply, QuickReplyButton, TextSendMessage
from pydantic import parse_obj_as

from config.settings import (
    BASE_PROJECT_URL,
    DB_LINE_ACCOUNTS,
    DB_REMINDERS,
    PostbackActionData,
)
from models import ReminderWithKeyModel, UserModel, UserWithKeyModel

from .base import EventHandlerMixinBase


class MessageEventHandlerMixin(EventHandlerMixinBase):
    async def _handle_normal_mode(self, event: MessageEvent, user: UserWithKeyModel):
        reply = [
            TextSendMessage(text=f"You: {event.message.text}"),
        ]
        await self.line_bot_api.reply_message(
            event.reply_token,
            reply,
        )

    async def _handle_memo_post_mode(self, event: MessageEvent, user: UserWithKeyModel):
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
        target_text = event.message.text.strip()
        if target_text:
            DB_LINE_ACCOUNTS.update(
                UserModel.construct(memos=user.memos + [target_text]).dict(),
                key=user.key,
            )
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"「{target_text}」を追加しました。\n\n終了したい場合は以下のボタンを押してください。",
                    quick_reply=quick_reply,
                ),
            )
        else:
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="有効な文を入力してください。\n\n終了したい場合は以下のボタンを押してください。",
                    quick_reply=quick_reply,
                ),
            )

    async def _handle_memo_deletion_mode(
        self, event: MessageEvent, user: UserWithKeyModel
    ):
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
        try:
            target_number = int(event.message.text)
            if target_number <= 0:
                raise ValueError(
                    "Invalid number. Valid if target_number is greater or equal to 0."
                )
            target_memo = user.memos.pop(target_number - 1)
            DB_LINE_ACCOUNTS.update(
                user.dict(include={"memos"}),
                key=user.key,
            )
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
                    text=(
                        f"「{target_number}:"
                        f" {target_memo}」を削除しました。\n\n{memo_list_text}\n\n終了したい場合は以下のボタンを押してください。"
                    ),
                    quick_reply=quick_reply,
                ),
            )
        except (ValueError, IndexError, TypeError):
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="有効な番号を入力してください。\n\n終了したい場合は以下のボタンを押してください。",
                    quick_reply=quick_reply,
                ),
            )

    async def _handle_reminder_post_content_mode(self, event: MessageEvent):
        quick_reply = QuickReply(
            items=[
                QuickReplyButton(
                    action=PostbackAction(
                        label="リマインダー追加を終了する",
                        data=PostbackActionData.terminate.value,
                    )
                ),
            ]
        )
        target_text = event.message.text.strip()
        if target_text:
            user_reminder = ReminderWithKeyModel.parse_obj(
                DB_REMINDERS.fetch({"line_user_id": self.user_id}).items[-1]
            )
            if user_reminder.content:
                await self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="日時が選択されていません。\n\n終了したい場合は以下のボタンを押してください。",
                        quick_reply=quick_reply,
                    ),
                )
            else:
                user_reminder.content = target_text
                DB_REMINDERS.update(
                    user_reminder.dict(include={"content"}),
                    key=user_reminder.key,
                )
                await self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text=(
                            f'「{(datetime.fromisoformat(user_reminder.datetime) + timedelta(hours=9)).strftime("%Y/%m/%d %H:%M")}\n{target_text}」を追加しました。\n\n終了したい場合は以下のボタンを押してください。'
                        ),
                        quick_reply=quick_reply,
                    ),
                )
        else:
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="有効な文を入力してください。\n\n終了したい場合は以下のボタンを押してください。",
                    quick_reply=quick_reply,
                ),
            )

    async def _handle_reminder_deletion_mode(self, event: MessageEvent):
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
        try:
            target_number = int(event.message.text)
            if target_number <= 0:
                raise ValueError(
                    "Invalid number. Valid if target_number is greater or equal to 0."
                )
            user_reminders_raw = DB_REMINDERS.fetch(
                {"line_user_id": self.user_id}
            ).items
            user_reminders = parse_obj_as(
                List[ReminderWithKeyModel], user_reminders_raw
            )
            target_user_reminder = user_reminders.pop(target_number - 1)
            DB_REMINDERS.delete(key=target_user_reminder.key)
            if user_reminders:
                reminder_list_text = "現在クラウドに保存されているリマインダーは↓\n"
                reminder_list_text += "\n".join(
                    f'{number}\n{(datetime.fromisoformat(reminder.datetime) + timedelta(hours=9)).strftime("%Y/%m/%d %H:%M")} {reminder.content}'
                    for number, reminder in enumerate(user_reminders, 1)
                )
            else:
                reminder_list_text = "クラウドに保存されているリマインダーはありません。"
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=(
                        f'「{target_number}\n{(datetime.fromisoformat(target_user_reminder.datetime) + timedelta(hours=9)).strftime("%Y/%m/%d %H:%M")} {target_user_reminder.content}」を削除しました。\n\n{reminder_list_text}\n\n終了したい場合は以下のボタンを押してください。'
                    ),
                    quick_reply=quick_reply,
                ),
            )
        except (ValueError, IndexError, TypeError):
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="有効な番号を入力してください。\n\n終了したい場合は以下のボタンを押してください。",
                    quick_reply=quick_reply,
                ),
            )

    async def _handle_file_post_mode(self, event: MessageEvent, user: UserWithKeyModel):
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
        if event.message.type == "image":
            stream_data = await self.line_bot_api.get_message_content(event.message.id)
            binary_data = b""
            async for b in stream_data.iter_content():
                binary_data += b
            if len(binary_data) + user.storage_capacity > 50 * 10**6:
                await self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="クラウドの合計で50MBを超えるため保存出来ませんでした。\n\n終了したい場合は以下のボタンを押してください。",
                        quick_reply=quick_reply,
                    ),
                )

            self.drive.put(
                name=f"{self.user_id}/{event.message.id}.jpeg",
                data=binary_data,
                content_type=stream_data.content_type,
            )
            user.storage_capacity += len(binary_data)
            DB_LINE_ACCOUNTS.update(
                user.dict(include={"storage_capacity"}), self.user_id
            )
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"{BASE_PROJECT_URL}/images/{event.message.id}.jpeg?token={user.token}\nに保存しました\n\n終了したい場合は以下のボタンを押してください。",
                    quick_reply=quick_reply,
                ),
            )
        elif event.message.type == "video":
            stream_data = await self.line_bot_api.get_message_content(event.message.id)
            binary_data = b""
            async for b in stream_data.iter_content():
                binary_data += b
            if len(binary_data) + user.storage_capacity > 50 * 10**6:
                await self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="クラウドの合計で50MBを超えるため保存出来ませんでした。\n\n終了したい場合は以下のボタンを押してください。",
                        quick_reply=quick_reply,
                    ),
                )

            self.drive.put(
                name=f"{self.user_id}/{event.message.id}.mp4",
                data=binary_data,
                content_type=stream_data.content_type,
            )
            user.storage_capacity += len(binary_data)
            DB_LINE_ACCOUNTS.update(
                user.dict(include={"storage_capacity"}), self.user_id
            )
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"{BASE_PROJECT_URL}/images/{event.message.id}.mp4?token={user.token}\nに保存しました\n\n終了したい場合は以下のボタンを押してください。",
                    quick_reply=quick_reply,
                ),
            )
        elif event.message.type == "audio":
            stream_data = await self.line_bot_api.get_message_content(event.message.id)
            binary_data = b""
            async for b in stream_data.iter_content():
                binary_data += b
            if len(binary_data) + user.storage_capacity > 50 * 10**6:
                await self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="クラウドの合計で50MBを超えるため保存出来ませんでした。\n\n終了したい場合は以下のボタンを押してください。",
                        quick_reply=quick_reply,
                    ),
                )

            self.drive.put(
                name=f"{self.user_id}/{event.message.id}.mp3",
                data=binary_data,
                content_type=stream_data.content_type,
            )
            print(stream_data.content_type)
            user.storage_capacity += len(binary_data)
            DB_LINE_ACCOUNTS.update(
                user.dict(include={"storage_capacity"}), self.user_id
            )
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"{BASE_PROJECT_URL}/images/{event.message.id}.mp3?token={user.token}\nに保存しました\n\n終了したい場合は以下のボタンを押してください。",
                    quick_reply=quick_reply,
                ),
            )
        elif event.message.type == "file":
            if event.message.file_size + user.storage_capacity > 50 * 10**6:
                await self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="クラウドの合計で50MBを超えるため保存出来ませんでした。\n\n終了したい場合は以下のボタンを押してください。",
                        quick_reply=quick_reply,
                    ),
                )
            stream_data = await self.line_bot_api.get_message_content(event.message.id)
            binary_data = b""
            async for b in stream_data.iter_content():
                binary_data += b

            extension: str = event.message.file_name.split(".")[-1]
            self.drive.put(
                name=f"{self.user_id}/{event.message.id}.{extension}",
                data=binary_data,
                content_type=stream_data.content_type,
            )
            user.storage_capacity += event.message.file_size
            DB_LINE_ACCOUNTS.update(
                user.dict(include={"storage_capacity"}), self.user_id
            )
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"{BASE_PROJECT_URL}/images/{event.message.id}.{extension}?token={user.token}\nに保存しました\n\n終了したい場合は以下のボタンを押してください。",
                    quick_reply=quick_reply,
                ),
            )
        else:
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="有効なファイルを送信してください。\n\n終了したい場合は以下のボタンを押してください。",
                    quick_reply=quick_reply,
                ),
            )

    async def _handle_file_deletion_mode(
        self, event: MessageEvent, user: UserWithKeyModel
    ):
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
                text="作成中です。\n\n終了したい場合は以下のボタンを押してください。",
                quick_reply=quick_reply,
            ),
        )

    async def handle_message_event(self, event: MessageEvent):
        user = UserWithKeyModel.parse_obj(DB_LINE_ACCOUNTS.get(self.user_id))
        if user.mode == PostbackActionData.normal.value:
            await self._handle_normal_mode(event, user)

        elif user.mode == PostbackActionData.memo_post.value:
            await self._handle_memo_post_mode(event, user)

        elif user.mode == PostbackActionData.memo_deletion.value:
            await self._handle_memo_deletion_mode(event, user)

        elif user.mode == PostbackActionData.reminder_post_content.value:
            await self._handle_reminder_post_content_mode(event)

        elif user.mode == PostbackActionData.reminder_deletion.value:
            await self._handle_reminder_deletion_mode(event)

        elif user.mode == PostbackActionData.file_post.value:
            await self._handle_file_post_mode(event, user)

        elif user.mode == PostbackActionData.file_deletion.value:
            await self._handle_file_deletion_mode(event, user)
