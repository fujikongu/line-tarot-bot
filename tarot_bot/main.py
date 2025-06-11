import sys
import os
import json
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

from genre_handlers import send_tarot_reading

app = Flask(__name__)

# 環境変数
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# グローバルセッション
user_sessions = {}

# GitHub からパスワードデータを取得
def load_passwords_from_github():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/password_issuer/passwords.json"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    content = response.json()["content"]
    from base64 import b64decode
    decoded_content = b64decode(content).decode("utf-8")
    return json.loads(decoded_content)

# GitHub にパスワードデータを更新
def update_passwords_on_github(passwords):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/password_issuer/passwords.json"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    sha = response.json()["sha"]

    updated_content = json.dumps(passwords, ensure_ascii=False, indent=2)
    from base64 import b64encode
    encoded_content = b64encode(updated_content.encode("utf-8")).decode("utf-8")

    data = {
        "message": "Update passwords.json",
        "content": encoded_content,
        "sha": sha
    }

    put_response = requests.put(url, headers=headers, data=json.dumps(data))
    put_response.raise_for_status()
    print(f"[DEBUG] GitHub update status: {put_response.status_code}")

# Webhook エンドポイント
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

    passwords_data = load_passwords_from_github()
    print(f"[DEBUG] Loaded passwords: {passwords_data}")

    # パスワード認証
    matched_password_entry = next((entry for entry in passwords_data if entry["password"] == user_message), None)

    if matched_password_entry:
        if not matched_password_entry["used"]:
            matched_password_entry["used"] = True
            update_passwords_on_github(passwords_data)

            # セッション状態にジャンル選択待ちを記録
            user_sessions[user_id] = "awaiting_genre"
            print("[DEBUG] Password matched → Sending genre selection")

            quick_reply_buttons = [
                QuickReplyButton(action=MessageAction(label="恋愛運", text="恋愛運")),
                QuickReplyButton(action=MessageAction(label="仕事運", text="仕事運")),
                QuickReplyButton(action=MessageAction(label="金運", text="金運")),
                QuickReplyButton(action=MessageAction(label="結婚", text="結婚")),
                QuickReplyButton(action=MessageAction(label="今日の運勢", text="今日の運勢"))
            ]

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="✅パスワード認証成功！ジャンルを選んでください。",
                    quick_reply=QuickReply(items=quick_reply_buttons)
                )
            )
        else:
            print("[DEBUG] Password already used → Inform user")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌このパスワードはすでに使用済みです。\nご利用には新しいチケットをご購入ください。")
            )
        return

    # セッション状態 → ジャンル選択中の場合
    if user_sessions.get(user_id) == "awaiting_genre":
        if user_message in ["恋愛運", "仕事運", "金運", "結婚", "今日の運勢"]:
            print(f"[DEBUG] Genre selected: {user_message} → Calling send_tarot_reading")
            send_tarot_reading(event, user_message)
            # セッションをクリア
            user_sessions.pop(user_id, None)
            return

    # パスワード・ジャンルに該当しない場合
    print("[DEBUG] Unrecognized input → Asking for password")
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="❌パスワードを入力してください。")
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
