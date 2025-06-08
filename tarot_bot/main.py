
import os
import json
import requests
import base64
import openai
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
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(PASSWORDS_URL, headers=headers)
    if response.status_code == 200:
        content = base64.b64decode(response.json()["content"])
        return json.loads(content)
    else:
        print("Error fetching passwords.json:", response.status_code)
        return []

def update_passwords(passwords):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(PASSWORDS_URL, headers=headers)
    if response.status_code == 200:
        sha = response.json()["sha"]
        updated_content = base64.b64encode(json.dumps(passwords, ensure_ascii=False, indent=2).encode()).decode()
        data = {
            "message": "Update passwords.json",
            "content": updated_content,
            "sha": sha
        }
        update_response = requests.put(PASSWORDS_URL, headers=headers, data=json.dumps(data))
        if update_response.status_code in [200, 201]:
            print("passwords.json updated successfully.")
        else:
            print("Error updating passwords.json:", update_response.status_code, update_response.text)

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
                    send_genre_selection(event)
                else:
                    reply_text = "❌このパスワードは既に使用されています。新しいパスワードをご購入ください。"
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
            else:
                reply_text = "❌無効なパスワードです。"
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        else:
            reply_text = "❌パスワードを入力してください。\n例：mem1091"
例：mem1091"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
    else:
        genre = text
        send_tarot_reading(event, genre)
        del user_states[user_id]

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
