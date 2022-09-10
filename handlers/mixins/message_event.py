from datetime import datetime, timedelta
from typing import List

from linebot.models.actions import PostbackAction
from linebot.models.events import MessageEvent
from linebot.models.send_messages import TextSendMessage, QuickReply, QuickReplyButton
from pydantic import parse_obj_as

from .base import EventHandlerMixinBase
from config.settings import BASE_PROJECT_URL, DB_LINE_ACCOUNTS, DB_REMINDERS, PostbackActionData
from models import ReminderWithKeyModel, UserModel, UserWithKeyModel

class MessageEventHandlerMixin(EventHandlerMixinBase):
    async def handle_message_event(self, event: MessageEvent):
        user = UserWithKeyModel.parse_obj(DB_LINE_ACCOUNTS.get(self.user_id))
        if user.mode == PostbackActionData.normal.value:
            if event.message.type == 'image':
                stream_data = await self.line_bot_api.get_message_content(event.message.id)
                binary_data = b''
                async for b in stream_data.iter_content():
                    binary_data += b
                file_name = self.drive.put(
                    name=f'{self.user_id}/{event.message.id}.jpeg',
                    data=binary_data,
                    content_type=stream_data.content_type,
                )
                await self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text=f'{BASE_PROJECT_URL}/images{file_name.replace(self.user_id, "", 1)}?token={user.token}\nに保存しました'
                    )
                )
            else:
                reply = [
                    TextSendMessage(text=f'You: {event.message.text}'),
                ]
                image_file_paths = self.drive.list(prefix=self.user_id)["names"]
                if image_file_paths:
                    reply.append(
                        TextSendMessage(
                            text="\n\n".join(map(lambda x: f'{BASE_PROJECT_URL}/images{x.replace(self.user_id, "", 1)}?token={user.token}', image_file_paths))
                        )
                    )
                else:
                    reply.append(
                        TextSendMessage(
                            text="クラウドに保存されている画像はありません。"
                        )
                    )

                await self.line_bot_api.reply_message(
                    event.reply_token,
                    reply,
                )
        elif user.mode == PostbackActionData.memo_post.value:
            quick_reply = QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(
                            label='メモ追加を終了する',
                            data=PostbackActionData.terminate.value,
                        )
                    ),
                ]
            )
            target_text = event.message.text.strip()
            if target_text:
                DB_LINE_ACCOUNTS.update(
                    UserModel.construct(
                        memos=user.memos + [target_text]
                    ).dict(),
                    key=user.key,
                )
                await self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text=f'「{target_text}」を追加しました。\n\n終了したい場合は以下のボタンを押してください。',
                        quick_reply=quick_reply,
                    ),
                )
            else:
                await self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text=f'有効な文を入力してください。\n\n終了したい場合は以下のボタンを押してください。',
                        quick_reply=quick_reply,
                    ),
                )
        elif user.mode == PostbackActionData.memo_deletion.value:
            quick_reply = QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(
                            label='メモ削除を終了する',
                            data=PostbackActionData.terminate.value,
                        )
                    ),
                ]
            )
            try:
                target_number = int(event.message.text)
                if target_number <= 0:
                    raise ValueError('Invalid number. Valid if target_number is greater or equal to 0.')
                target_memo = user.memos.pop(target_number - 1)
                DB_LINE_ACCOUNTS.update(
                    user.dict(include={'memos'}),
                    key=user.key,
                )
                if user.memos:
                    memo_list_text = '現在クラウドに保存されているメモは↓\n'
                    memo_list_text += '\n'.join(f'{number}: {value}' for number, value in enumerate(user.memos, 1))
                else:
                    memo_list_text = 'クラウドに保存されているメモはありません。'
                await self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text=f'「{target_number}: {target_memo}」を削除しました。\n\n{memo_list_text}\n\n終了したい場合は以下のボタンを押してください。',
                        quick_reply=quick_reply,
                    ),
                )
            except (ValueError, IndexError, TypeError):
                await self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text=f'有効な番号を入力してください。\n\n終了したい場合は以下のボタンを押してください。',
                        quick_reply=quick_reply,
                    ),
                )
        elif user.mode == PostbackActionData.reminder_post_content.value:
            quick_reply = QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(
                            label='リマインダー追加を終了する',
                            data=PostbackActionData.terminate.value,
                        )
                    ),
                ]
            )
            target_text = event.message.text.strip()
            if target_text:
                user_reminder = ReminderWithKeyModel.parse_obj(DB_REMINDERS.fetch({'line_user_id': self.user_id}).items[-1])
                if user_reminder.content:
                    await self.line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text=f'日時が選択されていません。\n\n終了したい場合は以下のボタンを押してください。',
                            quick_reply=quick_reply,
                        ),
                    )
                else:
                    user_reminder.content = target_text
                    DB_REMINDERS.update(
                        user_reminder.dict(include={'content'}),
                        key=user_reminder.key,
                    )
                    await self.line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text=f'「{(datetime.fromisoformat(user_reminder.datetime) + timedelta(hours=9)).strftime("%Y/%m/%d %H:%M")}\n{target_text}」を追加しました。\n\n終了したい場合は以下のボタンを押してください。',
                            quick_reply=quick_reply,
                        ),
                    )
            else:
                await self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text=f'有効な文を入力してください。\n\n終了したい場合は以下のボタンを押してください。',
                        quick_reply=quick_reply,
                    ),
                )
        elif user.mode == PostbackActionData.reminder_deletion.value:
            quick_reply = QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(
                            label='リマインダー削除を終了する',
                            data=PostbackActionData.terminate.value,
                        )
                    ),
                ]
            )
            try:
                target_number = int(event.message.text)
                if target_number <= 0:
                    raise ValueError('Invalid number. Valid if target_number is greater or equal to 0.')
                user_reminders_raw = DB_REMINDERS.fetch({'line_user_id': self.user_id}).items
                user_reminders = parse_obj_as(List[ReminderWithKeyModel], user_reminders_raw)
                target_user_reminder = user_reminders.pop(target_number - 1)
                DB_REMINDERS.delete(key=target_user_reminder.key)
                if user_reminders:
                    reminder_list_text = '現在クラウドに保存されているリマインダーは↓\n'
                    reminder_list_text += '\n'.join(
                        f'{number}\n{(datetime.fromisoformat(reminder.datetime) + timedelta(hours=9)).strftime("%Y/%m/%d %H:%M")} {reminder.content}'
                            for number, reminder in enumerate(user_reminders, 1)
                    )
                else:
                    reminder_list_text = 'クラウドに保存されているリマインダーはありません。'
                await self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text=f'「{target_number}\n{(datetime.fromisoformat(target_user_reminder.datetime) + timedelta(hours=9)).strftime("%Y/%m/%d %H:%M")} {target_user_reminder.content}」を削除しました。\n\n{reminder_list_text}\n\n終了したい場合は以下のボタンを押してください。',
                        quick_reply=quick_reply,
                    ),
                )
            except (ValueError, IndexError, TypeError):
                await self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text=f'有効な番号を入力してください。\n\n終了したい場合は以下のボタンを押してください。',
                        quick_reply=quick_reply,
                    ),
                )
