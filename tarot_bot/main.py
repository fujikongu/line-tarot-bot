
import os
import json
import requests
import base64
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction
)
from tarot_data import tarot_templates
from genre_handlers import handle_genre_selection

app = Flask(__name__)

# 環境変数の読み込み
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

PASSWORDS_URL = "https://api.github.com/repos/fujikongu/line-tarot-bot/contents/password_issuer/passwords.json"

def get_passwords():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(PASSWORDS_URL, headers=headers)
    if response.status_code == 200:
        content = response.json()["content"]
        decoded = base64.b64decode(content).decode("utf-8")
        return json.loads(decoded)
    return []

def update_password_state(password):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.get(PASSWORDS_URL, headers=headers)
    if response.status_code == 200:
        sha = response.json()["sha"]
        content = base64.b64decode(response.json()["content"]).decode("utf-8")
        passwords = json.loads(content)
        for entry in passwords:
            if entry["password"] == password:
                entry["state"] = "done"
        updated_content = base64.b64encode(json.dumps(passwords, ensure_ascii=False, indent=2).encode("utf-8")).decode("utf-8")
        data = {
            "message": "Update password state to done",
            "content": updated_content,
            "sha": sha
        }
        requests.put(PASSWORDS_URL, headers=headers, data=json.dumps(data))

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    passwords = get_passwords()
    for entry in passwords:
        if entry["password"] == text and entry.get("state") != "done":
            update_password_state(text)
            send_genre_selection(event)
            return
    if text in tarot_templates:
        handle_genre_selection(event, text)
        return
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="❌パスワードが無効です。正しいパスワードを入力してください。")
    )

def send_genre_selection(event):
    buttons = [
        QuickReplyButton(action=MessageAction(label=key, text=key))
        for key in tarot_templates
    ]
    message = TextSendMessage(
        text="✅パスワード認証成功！\nジャンルを選んでください。",
        quick_reply=QuickReply(items=buttons)
    )
    line_bot_api.reply_message(event.reply_token, message)

if __name__ == "__main__":
    app.run()
