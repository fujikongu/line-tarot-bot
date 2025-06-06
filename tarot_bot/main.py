
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
    print(f">>> GitHub API レスポンス内容: {response.text[:200]}")

    if response.status_code == 200:
        return json.loads(response.text), response.headers.get("ETag")
    else:
        print(">>> GitHub API からパスワード取得失敗")
        return [], None

# GitHub に passwords.json を更新
def update_passwords(passwords, etag):
    print(">>> GitHub API 更新開始")
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }

    # 現在の passwords.json を base64 エンコードして送信
    get_response = requests.get(GITHUB_API_URL, headers=headers)
    if get_response.status_code != 200:
        print(">>> GitHub API GET失敗")
        return False

    sha = get_response.json()["sha"]

    updated_content = json.dumps(passwords, ensure_ascii=False, indent=4)
    encoded_content = updated_content.encode("utf-8")
    base64_content = base64.b64encode(encoded_content).decode("utf-8")

    data = {
        "message": "Update passwords.json (used flag)",
        "content": base64_content,
        "sha": sha
    }

    put_response = requests.put(GITHUB_API_URL, headers=headers, data=json.dumps(data))
    print(f">>> GitHub API PUT ステータスコード: {put_response.status_code}")
    return put_response.status_code == 200 or put_response.status_code == 201

# ジャンル選択用 QuickReply を作成
def create_genre_quick_reply():
    genres = [
        "恋愛運",
        "仕事運",
        "金運",
        "今日の運勢",
        "結婚",
        "未来の恋愛"
    ]
    quick_reply_buttons = [
        QuickReplyButton(action=MessageAction(label=genre, text=genre)) for genre in genres
    ]
    return QuickReply(items=quick_reply_buttons)

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
        if pw_entry["password"] == user_message and pw_entry.get("used") == False:
            # 認証成功 → used: true に更新
            pw_entry["used"] = True
            update_passwords(passwords, etag)

            # ジャンル選択を送信
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="占いたいジャンルを選んでください。",
                    quick_reply=create_genre_quick_reply()
                )
            )
            print(">>> 認証成功 → ジャンル選択画面を送信")
            return

    # 認証失敗
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="パスワードが無効です。購入後の有効なパスワードを入力してください。")
    )
    print(">>> 認証失敗 → エラーメッセージ送信")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
