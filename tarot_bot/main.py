import os
import json
import requests
import base64

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

from .genre_handlers import send_tarot_reading

app = Flask(__name__)

# 環境変数
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Webhookエンドポイント
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# メッセージ受信時の処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()
    print(f"[DEBUG] Received message: {user_message}")

    # パスワード認証済みか確認（簡易化のために直接ジャンル判定のみで進める）
    valid_genres = ["恋愛運", "仕事運", "金運", "結婚", "今日の運勢"]
    if user_message in valid_genres:
        print(f"[DEBUG] Genre selected: {user_message} → Calling send_tarot_reading")
        send_tarot_reading(event, user_message)
    else:
        print(f"[DEBUG] Unrecognized input → Asking for password")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌パスワードを入力してください。")
        )

def update_passwords(passwords):
    url = "https://api.github.com/repos/あなたのGitHubユーザー名/line-tarot-bot/contents/passwords.json"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    sha = response.json()["sha"]

    encoded_content = json.dumps(passwords, ensure_ascii=False, indent=2).encode("utf-8")
    encoded_content_b64 = base64.b64encode(encoded_content).decode("utf-8")

    data = {
        "message": "Update used passwords",
        "content": encoded_content_b64,
        "sha": sha
    }

    put_response = requests.put(url, headers=headers, data=json.dumps(data))
    put_response.raise_for_status()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
