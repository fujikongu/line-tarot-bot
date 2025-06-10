
import os
import json
import requests
import base64
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

app = Flask(__name__)

# LINE Botのチャネルアクセストークンとシークレット
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# GitHubのpasswords.jsonのURL
PASSWORDS_URL = "https://api.github.com/repos/fujikongu/line-tarot-bot/contents/password_issuer/passwords.json"

# GitHub から passwords.json を取得
def get_passwords_from_github():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(PASSWORDS_URL, headers=headers)
    print(f"[DEBUG] GitHub API status: {r.status_code}")  # デバッグ
    r.raise_for_status()
    content = r.json()["content"]
    decoded_content = base64.b64decode(content).decode("utf-8")
    passwords = json.loads(decoded_content)
    print(f"[DEBUG] Loaded passwords: {passwords}")  # デバッグ
    return passwords

@app.route("/", methods=["GET"])
def index():
    return "LINE Tarot Bot is running."

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

    print(f"[DEBUG] Received message: {user_message}")  # デバッグ

    try:
        passwords = get_passwords_from_github()
    except Exception as e:
        print(f"[ERROR] Failed to fetch passwords.json: {e}")  # デバッグ
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="パスワード取得エラーが発生しました。しばらくしてからお試しください。")
        )
        return

    if user_message in passwords:
        print("[DEBUG] Password matched → Sending genre selection")  # デバッグ
        # 認証成功 → ジャンル選択クイックリプライ
        quick_reply_buttons = [
            QuickReplyButton(action=MessageAction(label=genre, text=genre))
            for genre in ["恋愛運", "仕事運", "金運", "結婚", "未来の恋愛", "今日の運勢"]
        ]
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="✅パスワード認証成功！ジャンルを選んでください。",
                quick_reply=QuickReply(items=quick_reply_buttons)
            )
        )
    elif user_message in ["恋愛運", "仕事運", "金運", "結婚", "未来の恋愛", "今日の運勢"]:
        print(f"[DEBUG] Genre selected: {user_message} → Calling send_tarot_reading")  # デバッグ
        from genre_handlers import send_tarot_reading
        send_tarot_reading(event, user_message)
    else:
        print("[DEBUG] Unrecognized input → Asking for password")  # デバッグ
        # 認証失敗
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌パスワードを入力してください。
例：mem1091")
        )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
