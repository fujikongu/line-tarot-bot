import os
import json
import requests
import base64
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

from genre_handlers import send_genre_selection, send_tarot_reading

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PASSWORDS_URL = "https://api.github.com/repos/fujikongu/line-tarot-bot/contents/password_issuer/passwords.json"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

user_states = {}

def get_passwords():
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw",
    }
    response = requests.get(PASSWORDS_URL, headers=headers)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        print("Failed to fetch passwords:", response.status_code)
        return []

def update_passwords(passwords):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    content = base64.b64encode(json.dumps(passwords, ensure_ascii=False, indent=4).encode("utf-8-sig")).decode("utf-8")
    data = {
        "message": "Update passwords.json",
        "content": content,
        "sha": get_passwords_sha(),
    }
    response = requests.put(PASSWORDS_URL, headers=headers, json=data)
    if response.status_code == 200 or response.status_code == 201:
        print("Passwords updated successfully")
    else:
        print("Failed to update passwords:", response.status_code, response.text)

def get_passwords_sha():
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    response = requests.get(PASSWORDS_URL, headers=headers)
    if response.status_code == 200:
        return response.json()["sha"]
    else:
        print("Failed to fetch SHA:", response.status_code)
        return None

@app.route("/callback", methods=["POST"])
def callback():
    body = request.get_data(as_text=True)
    signature = request.headers["X-Line-Signature"]

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()

    if user_id not in user_states:
        if text.startswith("mem") and len(text) == 7:
            passwords = get_passwords()
            password_entry = next((p for p in passwords if p["password"] == text), None)
            if password_entry:
                if not password_entry["used"]:
                    password_entry["used"] = True
                    update_passwords(passwords)
                    user_states[user_id] = "authenticated"
                    send_genre_selection(event, line_bot_api)
                else:
                    reply_text = "❌このパスワードは既に使用されています。新しいパスワードをご購入ください。"
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
            else:
                reply_text = "❌無効なパスワードです。"
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        else:
            reply_text = "❌パスワードを入力してください。"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
    else:
        genre = text
        send_tarot_reading(event, genre, line_bot_api)
        del user_states[user_id]

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
