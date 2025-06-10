import os
import json
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

app = Flask(__name__)

# 環境変数
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = "fujikongu"
REPO_NAME = "line-tarot-bot"
FILE_PATH = "password_issuer/passwords.json"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# パスワード取得関数
def fetch_passwords():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        print("[DEBUG] GitHub API status: 200")
        return json.loads(response.text)
    else:
        print(f"[DEBUG] GitHub API status: {response.status_code}")
        return []

# パスワード更新関数
def update_passwords(passwords):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    # 現在のファイル情報を取得してshaを得る
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        sha = response.json()["sha"]
    else:
        print(f"[DEBUG] Failed to get SHA, status code: {response.status_code}")
        return

    data = {
        "message": "Update passwords.json",
        "content": json.dumps(passwords, ensure_ascii=False, indent=2).encode("utf-8").decode("utf-8").encode("utf-8").decode("utf-8"),
        "sha": sha
    }
    put_response = requests.put(url, headers=headers, json=data)
    print(f"[DEBUG] GitHub update status: {put_response.status_code}")

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()
    print(f"[DEBUG] Received message: {user_message}")

    passwords = fetch_passwords()
    print(f"[DEBUG] Loaded passwords: {passwords}")

    # パスワード判定
    password_entry = next((p for p in passwords if p["password"] == user_message), None)
    if password_entry:
        if not password_entry["used"]:
            # パスワード未使用 → 使用済みに変更して保存
            password_entry["used"] = True
            update_passwords(passwords)

            print(f"[DEBUG] Password matched → Sending genre selection")

            # クイックリプライ送信
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
                    text="✅パスワード認証成功！
ジャンルを選んでください。",
                    quick_reply=QuickReply(items=quick_reply_buttons)
                )
            )
        else:
            print(f"[DEBUG] Password already used → Inform user")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="❌このパスワードはすでに使用済みです。
ご利用には新しいチケットをご購入ください。"
                )
            )
    # ジャンル判定
    elif user_message in ["恋愛運", "仕事運", "金運", "結婚", "今日の運勢"]:
        print(f"[DEBUG] Genre selected: {user_message} → Calling send_tarot_reading")
        from genre_handlers import send_tarot_reading
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