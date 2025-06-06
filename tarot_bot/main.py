
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

# GitHubリポジトリの情報
GITHUB_API_URL = "https://api.github.com/repos/fujikongu/line-tarot-bot/contents/password_issuer/passwords.json"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def get_passwords():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(GITHUB_API_URL, headers=headers)
    print(f"GitHub API response status: {response.status_code}")
    print(f"GitHub API response content: {response.text}")
    if response.status_code == 200:
        content = response.json()["content"]
        import base64
        decoded_content = base64.b64decode(content).decode("utf-8")
        passwords = json.loads(decoded_content)
        print(f"Loaded passwords: {passwords}")
        return passwords
    else:
        print(f"Failed to fetch passwords.json: {response.status_code} {response.text}")
        return []

@app.route("/")
def index():
    return "LINE Bot is running."

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
    text = event.message.text.strip()

    # 現在のパスワードリストをGitHubから取得
    passwords = get_passwords()

    # セッション管理用に仮のユーザーステート管理（メモリ上のみ簡易実装）
    if not hasattr(app, "user_states"):
        app.user_states = {}

    user_state = app.user_states.get(user_id, "waiting_for_password")

    if user_state == "waiting_for_password":
        if text in passwords:
            app.user_states[user_id] = "waiting_for_genre"
            quick_reply_buttons = [
                QuickReplyButton(action=MessageAction(label=genre, text=genre))
                for genre in ["恋愛運", "仕事運", "金運", "結婚", "未来の恋愛", "今日の運勢"]
            ]
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="ジャンルを選んでください：",
                    quick_reply=QuickReply(items=quick_reply_buttons)
                )
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="パスワードを入力してください。\n例：mem1091")
            )
    elif user_state == "waiting_for_genre":
        # ジャンル選択後の仮応答（ここに占い結果を入れる処理を実装可能）
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"「{text}」の占い結果は近日公開予定です。")
        )
        # 一度ジャンル選択後はリセットして再度パスワード待ちに戻す
        app.user_states[user_id] = "waiting_for_password"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
