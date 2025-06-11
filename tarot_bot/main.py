
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

# 状態管理
user_states = {}

# GitHub passwords.json URL
GITHUB_PASSWORDS_URL = "https://api.github.com/repos/fujikongu/line-tarot-bot/contents/password_issuer/passwords.json"

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
    print(f"[DEBUG] Received message: {user_message}")

    state = user_states.get(user_id, None)

    if state == "awaiting_genre":
        valid_genres = ["恋愛運", "仕事運", "金運", "結婚", "今日の運勢"]
        if user_message in valid_genres:
            print(f"[DEBUG] Genre selected: {user_message} → Calling send_tarot_reading")
            send_tarot_reading(event, user_message, line_bot_api)
            user_states.pop(user_id, None)
        else:
            print(f"[DEBUG] Unrecognized genre → Asking again")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌ジャンルを選択してください。（ボタンを押してください）")
            )
        return

    passwords = load_passwords()
    matched = False
    for pw_entry in passwords:
        if pw_entry["password"] == user_message:
            matched = True
            if pw_entry["used"]:
                print("[DEBUG] Password already used → Inform user")
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="❌このパスワードはすでに使用済みです。\nご利用には新しいチケットをご購入ください。")
                )
            else:
                print("[DEBUG] Password matched → Sending genre selection")
                pw_entry["used"] = True
                update_passwords(passwords)
                user_states[user_id] = "awaiting_genre"
                quick_reply_buttons = [
                    QuickReplyButton(action=MessageAction(label=genre, text=genre))
                    for genre in ["恋愛運", "仕事運", "金運", "結婚", "今日の運勢"]
                ]
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="✅パスワード認証成功！\nジャンルを選んでください。",
                        quick_reply=QuickReply(items=quick_reply_buttons)
                    )
                )
            break

    if not matched:
        print("[DEBUG] Password not matched → Asking again")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌パスワードを入力してください。")
        )

def load_passwords():
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(GITHUB_PASSWORDS_URL, headers=headers)
    response.raise_for_status()
    content = response.json()["content"]
    decoded_content = base64.b64decode(content).decode("utf-8")
    return json.loads(decoded_content)

def update_passwords(passwords):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(GITHUB_PASSWORDS_URL, headers=headers)
    response.raise_for_status()
    sha = response.json()["sha"]

    encoded_content = json.dumps(passwords, ensure_ascii=False, indent=2).encode("utf-8")
    encoded_content_b64 = base64.b64encode(encoded_content).decode("utf-8")

    data = {
        "message": "Update used passwords",
        "content": encoded_content_b64,
        "sha": sha
    }

    put_response = requests.put(GITHUB_PASSWORDS_URL, headers=headers, data=json.dumps(data))
    put_response.raise_for_status()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
