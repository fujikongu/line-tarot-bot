
import os
import json
import requests
from flask import Flask, request, abort

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

GITHUB_API_URL = os.getenv("GITHUB_API_URL")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def get_passwords():
    print(">>> GitHub API 呼び出し開始")
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    response = requests.get(GITHUB_API_URL, headers=headers)
    print(f">>> GitHub API ステータスコード: {response.status_code}")
    print(f">>> GitHub API レスポンス内容: {response.text[:200]}")

    if response.status_code == 200:
        return json.loads(response.text)
    else:
        print(">>> GitHub API からパスワード取得失敗")
        return []

@app.route("/callback", methods=["POST"])
def callback():
    print(">>> /callback エンドポイントにリクエスト受信")
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    print(f">>> 受信 body: {body}")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print(">>> InvalidSignatureError 発生")
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()
    print(f">>> ユーザーメッセージ: {user_message}")

    passwords = get_passwords()
    print(f">>> 現在のパスワードリスト: {passwords}")

    if user_message in passwords:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="✅ パスワード認証成功 🎉")
        )
        # GitHubのpasswords.json更新処理を本番ではここに入れる（省略）
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="パスワードを入力してください。\n例 : mem1091")
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
