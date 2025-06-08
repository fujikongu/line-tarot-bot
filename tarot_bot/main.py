
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

# 環境変数
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PASSWORDS_URL = "https://api.github.com/repos/fujikongu/line-tarot-bot/contents/password_issuer/passwords.json"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# GitHubからpasswords.json取得（キャッシュ対策ヘッダー付き）
def get_passwords():
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw",
        "Cache-Control": "no-cache"
    }
    response = requests.get(PASSWORDS_URL, headers=headers)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        print("Failed to fetch passwords.json:", response.status_code, response.text)
        return []

# GitHubにpasswords.jsonを更新
def update_passwords(passwords):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    # まず現在のSHAを取得
    sha_response = requests.get(PASSWORDS_URL, headers=headers)
    sha = sha_response.json()["sha"]

    content = base64.b64encode(json.dumps(passwords, indent=2, ensure_ascii=False).encode()).decode()

    data = {
        "message": "Update passwords.json",
        "content": content,
        "sha": sha
    }
    put_response = requests.put(PASSWORDS_URL, headers=headers, data=json.dumps(data))
    if put_response.status_code == 200 or put_response.status_code == 201:
        print("Successfully updated passwords.json")
    else:
        print("Failed to update passwords.json:", put_response.status_code, put_response.text)

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# ユーザーごとの状態管理
user_states = {}

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()

    # 1. パスワード待ち状態（初期状態）
    if user_id not in user_states:
        passwords = get_passwords()
        matching_pw = next((p for p in passwords if p["password"] == text), None)

        if matching_pw:
            if matching_pw["used"]:
                reply_text = "❌このパスワードは既に使用されています。新しいパスワードをご購入ください。"
            else:
                # パスワード使用済みに更新
                matching_pw["used"] = True
                update_passwords(passwords)

                user_states[user_id] = "awaiting_genre"
                send_genre_selection(event)
                return
        else:
            reply_text = "❌パスワードを入力してください。
例：mem1091"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
        return

    # 2. ジャンル選択中
    if user_states.get(user_id) == "awaiting_genre":
        genre = text
        send_tarot_reading(event, genre)
        user_states.pop(user_id, None)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
