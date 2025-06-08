
# main.py (正常版・utf-8-sig)

import os
import json
import requests
import base64
from flask import Flask, request, abort, render_template_string
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

from genre_handlers import send_genre_selection, send_tarot_reading

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

PASSWORDS_URL = "https://api.github.com/repos/fujikongu/line-tarot-bot/contents/password_issuer/passwords.json"

user_states = {}

def get_passwords():
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    response = requests.get(PASSWORDS_URL, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to fetch passwords.json")
        return []

def update_passwords(passwords):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    get_response = requests.get(PASSWORDS_URL, headers=headers)
    sha = get_response.json()["sha"]

    content = base64.b64encode(json.dumps(passwords, ensure_ascii=False, indent=2).encode("utf-8")).decode("utf-8")
    data = {
        "message": "Update passwords.json",
        "content": content,
        "sha": sha
    }
    response = requests.put(PASSWORDS_URL, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        print("Passwords updated successfully.")
    else:
        print(f"Failed to update passwords.json: {response.content}")

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
            reply_text = "❌パスワードを入力してください。
例：mem1091"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
    else:
        genre = text
        send_tarot_reading(event, genre)
        # del user_states[user_id]  # ここはコメントのまま保持OK

# 簡易パスワード発行画面
@app.route("/issue-password", methods=["GET", "POST"])
def issue_password():
    if request.method == "POST":
        import random
        new_password = f"mem{random.randint(1000,9999)}"

        passwords = get_passwords()
        passwords.append({"password": new_password, "used": False})
        update_passwords(passwords)

        return f"<h2>新しいパスワード: {new_password}</h2>"

    return render_template_string("""
        <h2>パスワード発行</h2>
        <form method="post">
            <button type="submit">発行する</button>
        </form>
    """)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
