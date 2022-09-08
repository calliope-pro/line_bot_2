import os
from datetime import datetime
from typing import List
from uuid import uuid4

from cryptocode import decrypt, encrypt
from deta import _Drive
from linebot import AsyncLineBotApi
from linebot.models.actions import PostbackAction, DatetimePickerAction
from linebot.models.events import Event, MessageEvent, FollowEvent, PostbackEvent
from linebot.models.send_messages import TextSendMessage, QuickReply, QuickReplyButton

from models import ReminderModel, ReminderWithKeyModel, UserModel, UserWithKeyModel
from pydantic import parse_obj_as
from settings import BASE_PROJECT_URL, DB_LINE_ACCOUNTS, DB_REMINDERS, IS_MAINTENANCE, PostbackActionData

class EventsHandler:
    def __init__(self, line_bot_api: AsyncLineBotApi, events: List[Event], drive: _Drive):
        self.line_bot_api = line_bot_api
        self.events = events
        self.drive = drive
        self.user_id = None

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
                    UserModel.construct(
                        memos=user.memos
                    ).dict(),
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
                user_reminder = ReminderWithKeyModel.parse_obj(DB_REMINDERS.fetch({'line_user_id': self.user_id}).last)
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
                        user_reminder.content,
                        key=user_reminder.key,
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

    async def handle_follow_event(self, event: FollowEvent):
        DB_LINE_ACCOUNTS.put(
            UserModel(
                token=str(uuid4()),
                mode=PostbackActionData.normal.value,
                memos=[]
            ).dict(),
            key=self.user_id
        )

        await self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f'Welcome!'),
        )
    
    async def handle_postback_event(self, event: PostbackEvent):
        data = event.postback.data
        if data == PostbackActionData.memo.value:
            quick_reply = QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(
                            label='メモ一覧',
                            data=PostbackActionData.memo_list.value,
                        )
                    ),
                    QuickReplyButton(
                        action=PostbackAction(
                            label='メモ追加',
                            data=PostbackActionData.memo_post.value,
                        )
                    ),
                    QuickReplyButton(
                        action=PostbackAction(
                            label='メモ削除',
                            data=PostbackActionData.memo_deletion.value,
                        )
                    ),
                ]
            )
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text='メモ機能の何を使いますか？',
                    quick_reply=quick_reply,
                )
            )
        elif data == PostbackActionData.memo_list.value:
            user = UserWithKeyModel.parse_obj(DB_LINE_ACCOUNTS.get(self.user_id))
            if user.memos:
                memo_list_text = '現在クラウドに保存されているメモは↓\n'
                memo_list_text += '\n'.join(f'{number}: {value}' for number, value in enumerate(user.memos, 1))
            else:
                memo_list_text = 'クラウドに保存されているメモはありません。'
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=memo_list_text,
                )
            )
        elif data == PostbackActionData.memo_post.value:
            DB_LINE_ACCOUNTS.update(
                UserModel.construct(
                    mode=PostbackActionData.memo_post.value).dict(),
                key=self.user_id
            )
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
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text='メモしたいことを入力してください。\n\n終了したい場合は以下のボタンを押してください。',
                    quick_reply=quick_reply,
                )
            )
        elif data == PostbackActionData.memo_deletion.value:
            DB_LINE_ACCOUNTS.update(
                UserModel.construct(
                    mode=PostbackActionData.memo_deletion.value).dict(),
                key=self.user_id
            )
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
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text='削除したいメモの番号を入力してください。\n\n終了したい場合は以下のボタンを押してください。',
                    quick_reply=quick_reply,
                )
            )
        elif data == PostbackActionData.reminder.value:
            try:
                assert self.user_id == os.environ['MY_LINE_USER_ID'], 'user_idが異なります'
            except AssertionError as e:
                print(e)
                print(f'{event.source.user_id}から発信')
                await self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="403 Forbidden\nYou have no authority.")
                )

            quick_reply = QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(
                            label='リマインダー一覧',
                            data=PostbackActionData.reminder_list.value,
                        )
                    ),
                    QuickReplyButton(
                        action=DatetimePickerAction(
                            label='リマインダー追加',
                            data=PostbackActionData.reminder_post_content.value,
                            mode='datetime',
                        )
                    ),
                    QuickReplyButton(
                        action=PostbackAction(
                            label='リマインダー削除',
                            data=PostbackActionData.reminder_deletion.value,
                        )
                    ),
                ]
            )
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text='リマインダー機能の何を使いますか？',
                    quick_reply=quick_reply,
                )
            )
        elif data == PostbackActionData.reminder_list.value:
            user_reminders_raw = DB_REMINDERS.fetch({'line_user_id': self.user_id}).items
            user_reminders = parse_obj_as(List[ReminderWithKeyModel], user_reminders_raw)
            if user_reminders:
                reminder_list_text = '現在クラウドに保存されているリマインダーは↓\n'
                reminder_list_text += '\n'.join(f'{number}:\n{reminder.datetime} {reminder.content}' for number, reminder in enumerate(user_reminders, 1))
            else:
                reminder_list_text = 'クラウドに保存されているリマインダーはありません。'
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=reminder_list_text,
                )
            )
        elif data == PostbackActionData.reminder_post_content.value:
            user_reminders_raw = DB_REMINDERS.fetch({'line_user_id': self.user_id}).items
            user_reminders = parse_obj_as(List[ReminderWithKeyModel], user_reminders_raw)
            print(event.postback.params['datetime'])
            DB_REMINDERS.put(
                ReminderModel(
                    datetime=event.postback.params['datetime'],
                    content='',
                    line_user_id=self.user_id,
                ).dict(),
                key=str(datetime.now().timestamp())
            )
            print(6178)
            DB_LINE_ACCOUNTS.update(
                UserModel.construct(
                    mode=PostbackActionData.reminder_post_content.value
                ).dict(),
                key=self.user_id
            )
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text='リマインドしたいことを入力してください。',
                )
            )
        elif data == PostbackActionData.usage.value:
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    '''このcalliope_botは現在大きく3つの機能を有しております。
①写真を投稿することで自動的にクラウドに保存され、保存先がurlとして取得できます。平常時メッセージを送った際には、クラウドに保存されている全ての画像のurlを取得できます。
②メモ一覧, 追加, 削除がリッチメニューを通して操作できます。
③時間を設定しリマインダーを登録することができます。(作成中)'''
                )
            )
        elif data == PostbackActionData.terminate.value:
            DB_LINE_ACCOUNTS.update(
                UserModel.construct(
                    mode=PostbackActionData.normal.value).dict(),
                key=self.user_id
            )
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='終了しました。')
            )

    async def handler(self):
        # ベント処理List[Event]
        for event in self.events:
            if IS_MAINTENANCE:
                try:
                    assert event.source.user_id == os.environ['MY_LINE_USER_ID'], 'user_idが異なります'
                except AssertionError as e:
                    print(e)
                    print(f'{event.source.user_id}から発信')
                    await self.line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="403 Forbidden\nYou have no authority.")
                    )
                    break

            self.user_id = event.source.user_id

            # メッセージイベント
            if isinstance(event, MessageEvent):
                await self.handle_message_event(event)
                break
            # ポストバックイベント
            elif isinstance(event, PostbackEvent):
                await self.handle_postback_event(event)
                break
            # 友達追加イベント
            elif isinstance(event, FollowEvent):
                await self.handle_follow_event(event)
                break

