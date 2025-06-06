
import os
import json
import requests
from flask import Flask, request, abort

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

GITHUB_API_URL = os.getenv("GITHUB_API_URL")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# GitHub から passwords.json を取得
def get_passwords():
    print(">>> GitHub API 呼び出し開始")
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    response = requests.get(GITHUB_API_URL, headers=headers)
    print(f">>> GitHub API ステータスコード: {response.status_code}")
    print(f">>> GitHub API レスポンス内容: {response.text[:500]}")

    if response.status_code == 200:
        return json.loads(response.text), response.headers.get("ETag")
    else:
        print(">>> GitHub API からパスワード取得失敗")
        return [], None

# Webhook エンドポイント
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    print(f">>> Request body: {body}")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# MessageEvent handler
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()
    print(f">>> ユーザーメッセージ受信: {user_message}")

    passwords, etag = get_passwords()
    if not passwords:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="現在システムエラーのため認証ができません。しばらくしてから再試行してください。")
        )
        return

    # パスワード認証処理
    for pw_entry in passwords:
        # print 各エントリ確認用
        print(f">>> Checking pw_entry: {pw_entry}")
        if pw_entry.get("password") == user_message and pw_entry.get("used") == False:
            # 認証成功 → used: true に更新 (※ 今は更新せず確認だけ）
            pw_entry["used"] = True
            # 通知送信
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="認証成功！ジャンル選択画面はまだ準備中です（デバッグ中）"
                )
            )
            print(">>> 認証成功！")
            return

    # 認証失敗
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="パスワードが無効です。購入後の有効なパスワードを入力してください。")
    )
    print(">>> 認証失敗 → エラーメッセージ送信")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
