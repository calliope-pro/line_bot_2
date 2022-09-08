import os
from typing import List
from uuid import uuid4

from cryptocode import decrypt, encrypt
from deta import _Base, _Drive
from linebot import AsyncLineBotApi
from linebot.models.actions import PostbackAction
from linebot.models.events import Event, MessageEvent, FollowEvent, PostbackEvent
from linebot.models.send_messages import TextSendMessage, QuickReply, QuickReplyButton
from models import UserModel, UserWithKeyModel

from settings import BASE_PROJECT_URL, Mode

class EventsHandler:
    def __init__(self, line_bot_api: AsyncLineBotApi, events: List[Event], db: _Base, drive: _Drive):
        self.line_bot_api = line_bot_api
        self.events = events
        self.db = db
        self.drive = drive
        self.user_id = None

    async def handle_message_event(self, event: MessageEvent):
        user = UserWithKeyModel.parse_obj(self.db.get(self.user_id))
        if user.mode == Mode.normal.value:
            if event.message.type == 'image':
                data = await self.line_bot_api.get_message_content(event.message.id)
                binary_data = b''
                async for b in data.iter_content():
                    binary_data += b
                file_name = self.drive.put(
                    name=f'{self.user_id}/{event.message.id}.jpeg',
                    data=binary_data,
                    content_type=data.content_type,
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
        elif user.mode == Mode.memo_post.value:
            self.db.update(
                UserModel.construct(
                    memos=user.memos + [event.message.text]
                ).dict(),
                key=user.key,
            )
            quick_reply = QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(
                            label='メモ追加を終了する',
                            data='terminate',
                        )
                    ),
                ]
            )
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f'「{event.message.text}」を追加しました。\n終了したい場合は以下のボタンを押してください。',
                    quick_reply=quick_reply,
                ),
            )

    async def handle_follow_event(self, event: FollowEvent):
        self.db.put(
            UserModel(
                token=str(uuid4()),
                mode=Mode.normal.value,
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
        if data == 'memo':
            quick_reply = QuickReply(
                items=[
                    QuickReplyButton(
                        action=PostbackAction(
                            label='メモ一覧',
                            data='memo_list',
                        )
                    ),
                    QuickReplyButton(
                        action=PostbackAction(
                            label='メモ追加',
                            data='memo_post',
                        )
                    ),
                    QuickReplyButton(
                        action=PostbackAction(
                            label='メモ削除',
                            data='memo_deletion',
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
        elif data == 'memo_list':
            user = UserWithKeyModel.parse_obj(self.db.get(self.user_id))
            if user.memos:
                text = '\n'.join(f'{idx}: {value}' for idx, value in enumerate(user.memos, 1))
            else:
                text = 'クラウドに保存されているメモはありません。'
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=text,
                )
            )
        elif data == Mode.memo_post.value:
            self.db.update(
                UserModel.construct(
                    mode=Mode.memo_post.value).dict(),
                key=self.user_id
            )
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text='メモしたいことを入力してください',
                )
            )
        elif data == Mode.memo_deletion.value:
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text='削除したいメモの番号を入力してください',
                )
            )
        elif data == 'reminder':
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text='どういう用件ですか？',
                )
            )
        elif data == 'usage':
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    '''このcalliope_botは現在大きく3つの機能を有しております。
①写真を投稿することで自動的にクラウドに保存され、保存先がurlとして取得できます。平常時メッセージを送った際には、クラウドに保存されている全ての画像のurlを取得できます。
②メモ一覧, 追加, 削除がリッチメニューを通して操作できます。(作成中)
③時間を設定しリマインダーを登録することができます。(作成中)'''
                )
            )
        elif data == 'terminate':
            self.db.update(
                UserModel.construct(
                    mode=Mode.normal.value).dict(),
                key=self.user_id
            )
            await self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='終了しました。')
            )

    async def handler(self):
        # ベント処理List[Event]
        for event in self.events:
            try:
                assert event.source.user_id == os.environ['MY_LINE_USER_ID'], 'user_idが異なります'
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

            except AssertionError as e:
                print(e)
                print(f'{event.source.user_id}から発信')
                await self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="403 Forbidden\nYou have no authority.")
                )
                break
