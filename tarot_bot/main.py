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

PASSWORDS_URL = "https://raw.githubusercontent.com/fujikongu/line-tarot-bot/main/password_issuer/passwords.json"

def load_passwords():
    response = requests.get(PASSWORDS_URL)
    print(f"[DEBUG] GitHub API status: {response.status_code}")
    return response.json()

def update_passwords(passwords):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    update_url = "https://api.github.com/repos/fujikongu/line-tarot-bot/contents/password_issuer/passwords.json"
    response = requests.get(update_url, headers=headers)
    sha = response.json()["sha"]

    update_data = {
        "message": "Update passwords",
        "content": base64.b64encode(json.dumps(passwords, ensure_ascii=False, indent=4).encode()).decode(),
        "sha": sha
    }

    put_response = requests.put(update_url, headers=headers, json=update_data)
    print(f"[DEBUG] GitHub update status: {put_response.status_code}")

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
    user_message = event.message.text.strip()
    print(f"[DEBUG] Received message: {user_message}")

    passwords = load_passwords()
    matched = False

    for entry in passwords:
        if entry["password"] == user_message:
            matched = True
            if not entry["used"]:
                entry["used"] = True
                update_passwords(passwords)

                quick_reply_buttons = [
                    QuickReplyButton(action=MessageAction(label="恋愛運", text="恋愛運")),
                    QuickReplyButton(action=MessageAction(label="仕事運", text="仕事運")),
                    QuickReplyButton(action=MessageAction(label="金運", text="金運")),
                    QuickReplyButton(action=MessageAction(label="結婚", text="結婚")),
                    QuickReplyButton(action=MessageAction(label="今日の運勢", text="今日の運勢")),
                ]
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="✅パスワード認証成功！\nジャンルを選んでください。",
                        quick_reply=QuickReply(items=quick_reply_buttons)
                    )
                )
            else:
                print(f"[DEBUG] Password already used → Inform user")
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="❌このパスワードはすでに使用済みです。\nご利用には新しいチケットをご購入ください。")
                )
            break

    if not matched:
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

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
