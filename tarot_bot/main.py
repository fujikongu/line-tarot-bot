
import os
import json
import requests
import base64
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from genre_handlers import send_genre_selection

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL")
PASSWORDS_JSON_URL = GITHUB_REPO_URL.replace("github.com", "api.github.com/repos") + "/contents/password_issuer/passwords.json"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def get_valid_passwords():
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    response = requests.get(PASSWORDS_JSON_URL, headers=headers)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        print(f"Failed to fetch passwords.json: {response.status_code}")
        return {}

used_passwords = []

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()
    valid_passwords = get_valid_passwords()
    user_id = user_message

    if user_id in valid_passwords and user_id not in used_passwords:
        used_passwords.append(user_id)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"受付けました: {user_message}")
        )
        # ジャンル選択を送信（この1行を追加）
        send_genre_selection(event)

    elif user_id in used_passwords:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="このパスワードはすでに使用されています。")
        )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="無効なパスワードです。")
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
