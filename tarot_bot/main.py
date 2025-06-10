
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

# GitHub から passwords.json を取得 + SHAも返す
def get_passwords_from_github():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(PASSWORDS_URL, headers=headers)
    print(f"[DEBUG] GitHub API status: {r.status_code}")
    r.raise_for_status()
    content = r.json()["content"]
    sha = r.json()["sha"]
    decoded_content = base64.b64decode(content).decode("utf-8")
    passwords = json.loads(decoded_content)
    print(f"[DEBUG] Loaded passwords: {passwords}")
    return passwords, sha

# GitHub に passwords.json を更新
def update_passwords_on_github(passwords, sha):
    updated_content = base64.b64encode(json.dumps(passwords, indent=4, ensure_ascii=False).encode("utf-8")).decode("utf-8")
    update_headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    update_data = {
        "message": "Update used password",
        "content": updated_content,
        "sha": sha
    }
    response = requests.put(PASSWORDS_URL, headers=update_headers, json=update_data)
    print(f"[DEBUG] GitHub update status: {response.status_code}")
    response.raise_for_status()

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

    try:
        passwords, sha = get_passwords_from_github()
    except Exception as e:
        print(f"[ERROR] Failed to fetch passwords.json: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="パスワード取得エラーが発生しました。しばらくしてからお試しください。")
        )
        return

    print(f"[DEBUG] Received message: {user_message}")

    # ① ジャンル選択処理
    if user_message in ["恋愛運", "仕事運", "金運", "結婚", "今日の運勢"]:
        print(f"[DEBUG] Genre selected: {user_message} → Calling send_tarot_reading")
        from genre_handlers import send_tarot_reading
        send_tarot_reading(event, user_message)
        return

    # ② パスワード認証チェック
    matched_password_entry = None
    for pw_entry in passwords:
        if pw_entry["password"] == user_message and pw_entry["used"] == False:
            matched_password_entry = pw_entry
            break

    if matched_password_entry:
        print(f"[DEBUG] Password matched → Sending genre selection")
        matched_password_entry["used"] = True  # used を True に変更
        update_passwords_on_github(passwords, sha)  # GitHub に更新

        quick_reply_buttons = [
            QuickReplyButton(action=MessageAction(label=genre, text=genre))
            for genre in ["恋愛運", "仕事運", "金運", "結婚", "今日の運勢"]
        ]
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="✅パスワード認証成功！ジャンルを選んでください。",
                quick_reply=QuickReply(items=quick_reply_buttons)
            )
        )
    else:
        print(f"[DEBUG] Unrecognized input → Asking for password")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌パスワードを入力してください。")
        )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
