
import os
import json
import requests
import base64
import random
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# GitHub上のpasswords.json URL
PASSWORDS_URL = "https://raw.githubusercontent.com/fujikongu/line-tarot-bot/main/password_issuer/passwords.json"

# GitHubからpasswords.jsonを取得
def get_passwords():
    response = requests.get(PASSWORDS_URL)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        return []

# Webhookエンドポイント
@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# メッセージイベントのハンドラー
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()

    # パスワード認証
    if text.startswith("mem"):
        passwords = get_passwords()
        if text in passwords:
            # 認証成功 → ジャンル選択ボタンを表示
            reply_text = "✅ パスワード認証成功！ジャンルを選んでください。"
            quick_reply = QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="恋愛運", text="恋愛運")),
                QuickReplyButton(action=MessageAction(label="仕事運", text="仕事運")),
                QuickReplyButton(action=MessageAction(label="金運", text="金運")),
                QuickReplyButton(action=MessageAction(label="今日の運勢", text="今日の運勢")),
                QuickReplyButton(action=MessageAction(label="結婚", text="結婚")),
            ])
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text, quick_reply=quick_reply)
            )
            return

    # それ以外は簡易返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="メッセージを受け取りました。")
    )

if __name__ == "__main__":
    app.run()
