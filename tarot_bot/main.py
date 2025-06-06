
import os
import json
import requests
import base64
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# LINE Botのチャンネルアクセストークンとシークレット
YOUR_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
YOUR_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

# GitHub情報
GITHUB_API_URL = "https://api.github.com/repos/fujikongu/line-tarot-bot/contents/password_issuer/passwords.json"
GITHUB_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")

def get_passwords_from_github():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(GITHUB_API_URL, headers=headers)
    response.raise_for_status()
    content = response.json()["content"]
    decoded_content = base64.b64decode(content).decode("utf-8")
    return json.loads(decoded_content)

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
    user_message = event.message.text.strip()

    if user_message.startswith("mem"):
        try:
            passwords = get_passwords_from_github()
            print(f"[DEBUG] 現在のパスワードリスト: {passwords}")

            if user_message in passwords:
                # パスワード一致時の処理
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="✅ パスワード認証成功！ジャンルを選んでください：\n1️⃣ 恋愛運\n2️⃣ 仕事運\n3️⃣ 金運\n4️⃣ 結婚\n5️⃣ 未来の恋愛\n6️⃣ 今日の運勢")
                )
            else:
                # パスワード不一致
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="パスワードを入力してください。\n例：mem1091")
                )
        except Exception as e:
            print(f"[ERROR] GitHubからパスワード取得失敗: {e}")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="パスワード取得エラーが発生しました。時間をおいてお試しください。")
            )
    else:
        # 通常メッセージ処理（パスワード入力待ち）
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="パスワードを入力してください。\n例：mem1091")
        )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
