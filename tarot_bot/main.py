
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

# LINE Botのチャネルアクセストークンとシークレット
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# GitHubのpasswords.jsonのURL
PASSWORDS_URL = "https://api.github.com/repos/fujikongu/line-tarot-bot/contents/password_issuer/passwords.json"

# GitHub から passwords.json を取得
def get_passwords_from_github():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(PASSWORDS_URL, headers=headers)
    print(f"GitHub API status: {r.status_code}")
    r.raise_for_status()
    content = r.json()["content"]
    decoded_content = base64.b64decode(content).decode("utf-8")
    passwords = json.loads(decoded_content)
    print(f"Loaded passwords: {passwords}")
    return passwords

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
        passwords = get_passwords_from_github()
    except Exception as e:
        print(f"[ERROR] Failed to fetch passwords.json: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="パスワード取得エラーが発生しました。しばらくしてからお試しください。")
        )
        return

    if user_message in passwords:
        # 認証成功 → パスワード使用済みに更新
        passwords[user_message] = True
        try:
            update_passwords_on_github(passwords)
        except Exception as e:
            print(f"[ERROR] Failed to update passwords.json: {e}")

        # ジャンル選択画面へ
        send_genre_selection(event, line_bot_api)

    elif user_message in ["恋愛運", "仕事運", "金運", "結婚", "今日の運勢"]:
        send_tarot_reading(event, user_message, line_bot_api)

    else:
        # 認証失敗 or 通常メッセージ
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌パスワードを入力してください。\n例：mem1091")
        )

# GitHub に passwords.json を更新
def update_passwords_on_github(passwords):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(PASSWORDS_URL, headers=headers)
    r.raise_for_status()
    sha = r.json()["sha"]

    updated_content = json.dumps(passwords, ensure_ascii=False, indent=2)
    b64_content = base64.b64encode(updated_content.encode("utf-8")).decode("utf-8")

    data = {
        "message": "Update passwords.json",
        "content": b64_content,
        "sha": sha
    }

    put_r = requests.put(PASSWORDS_URL, headers=headers, data=json.dumps(data))
    put_r.raise_for_status()
    print(f"Updated passwords.json successfully.")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
