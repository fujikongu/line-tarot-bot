import os
import json
import requests
import base64
from flask import Flask, request, abort

from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

app = Flask(__name__)

# LINE APIの設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# GitHub passwords.json URL
PASSWORDS_URL = "https://api.github.com/repos/fujikongu/line-tarot-bot/contents/password_issuer/passwords.json"

# GitHub から passwords.json を取得
def get_passwords():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(PASSWORDS_URL, headers=headers)
    if response.status_code == 200:
        content = response.json()["content"]
        return json.loads(base64.b64decode(content).decode())
    else:
        return []

# /callback route (重要！)
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except Exception as e:
        app.logger.error("Error: " + str(e))
        abort(400)

    return "OK"

# パスワードリストの初期化
used_passwords = []

# メッセージイベントの処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global used_passwords
    user_message = event.message.text

    # GitHubから最新のパスワードリストを取得
    passwords = get_passwords()

    # パスワード認証
    if user_message in passwords and user_message not in used_passwords:
        used_passwords.append(user_message)
        reply_text = "✅パスワード認証成功！\nジャンルを選んでください。"
        quick_reply = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="恋愛運", text="恋愛運")),
            QuickReplyButton(action=MessageAction(label="仕事運", text="仕事運")),
            QuickReplyButton(action=MessageAction(label="金運", text="金運")),
            QuickReplyButton(action=MessageAction(label="結婚", text="結婚")),
            QuickReplyButton(action=MessageAction(label="未来の恋愛", text="未来の恋愛")),
            QuickReplyButton(action=MessageAction(label="今日の運勢", text="今日の運勢")),
        ])
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text, quick_reply=quick_reply)
        )
    elif user_message in used_passwords:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="⚠️このパスワードは既に使用されています。")
        )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌パスワードを入力してください。")
        )

# アプリ起動
if __name__ == "__main__":
    app.run()