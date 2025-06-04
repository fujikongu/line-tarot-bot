import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
)
from genre_handlers import get_tarot_response_by_genre

app = Flask(__name__)

# 環境変数からキーを取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ユーザーごとの状態管理用
user_states = {}

@app.route("/")
def home():
    return "LINEタロットBotは稼働中です。"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text.strip()

    # ユーザーがジャンル選択中であれば処理
    if user_id in user_states and user_states[user_id] == "awaiting_genre":
        genre = user_message
        response = get_tarot_response_by_genre(genre)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response)
        )
        del user_states[user_id]
        return

    # ジャンル選択を促すクイックリプライを送信
    user_states[user_id] = "awaiting_genre"
    reply_text = "ジャンルを選んでください："
    quick_reply_buttons = QuickReply(
        items=[
            QuickReplyButton(action=MessageAction(label="恋愛運", text="恋愛運")),
            QuickReplyButton(action=MessageAction(label="仕事運", text="仕事運")),
            QuickReplyButton(action=MessageAction(label="金運", text="金運")),
            QuickReplyButton(action=MessageAction(label="結婚・未来の恋愛", text="結婚・未来の恋愛")),
            QuickReplyButton(action=MessageAction(label="今日の運勢", text="今日の運勢")),
        ]
    )
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text, quick_reply=quick_reply_buttons)
    )

if __name__ == "__main__":
    app.run()