
import os
import json
import base64
import requests
from flask import Flask, request, abort

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

app = Flask(__name__)

# 環境変数から各種トークンを取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# GitHub URL を設定
GITHUB_URL = "https://api.github.com/repos/fujikongu/line-tarot-bot/contents/password_issuer/passwords.json"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# GitHubからpasswords.jsonを取得
def get_passwords():
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    response = requests.get(GITHUB_URL, headers=headers)
    if response.status_code == 200:
        content_json = response.json()
        content_encoded = content_json["content"]
        content_decoded = base64.b64decode(content_encoded).decode("utf-8")
        return json.loads(content_decoded)
    else:
        print(f"Failed to fetch passwords.json: {response.status_code}, {response.text}")
        return []

# GitHubにpasswords.jsonを書き戻す
def update_passwords(passwords):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    # まず最新SHAを取得
    get_response = requests.get(GITHUB_URL, headers=headers)
    if get_response.status_code == 200:
        sha = get_response.json()["sha"]
    else:
        print(f"Failed to get SHA: {get_response.status_code}, {get_response.text}")
        return

    # 更新する内容
    updated_content = base64.b64encode(json.dumps(passwords, indent=2).encode("utf-8")).decode("utf-8")
    data = {
        "message": "Update passwords.json",
        "content": updated_content,
        "sha": sha
    }
    put_response = requests.put(GITHUB_URL, headers=headers, json=data)
    if put_response.status_code not in [200, 201]:
        print(f"Failed to update passwords.json: {put_response.status_code}, {put_response.text}")

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

    passwords = get_passwords()
    if user_message in passwords:
        # 正しいパスワード → 使用済みにする
        passwords.remove(user_message)
        update_passwords(passwords)

        # ジャンル選択のクイックリプライ
        reply_text = "ジャンルを選択してください。"
        quick_reply_buttons = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label=genre, text=genre))
            for genre in ["恋愛運", "仕事運", "金運", "結婚", "未来の恋愛", "今日の運勢"]
        ])

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text, quick_reply=quick_reply_buttons)
        )
    else:
        # パスワードが違う or すでに使われた
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="パスワードを入力してください。\n例：mem1091")
        )

@app.route("/issue-password", methods=["GET"])
def issue_password():
    passwords = get_passwords()
    if passwords:
        new_password = passwords.pop(0)
        update_passwords(passwords)
        return f"Issued password: {new_password}"
    else:
        return "No passwords available.", 404

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
