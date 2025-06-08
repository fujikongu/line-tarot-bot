
import os
import json
import requests
from flask import Flask, request, abort

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

app = Flask(__name__)

# 環境変数からトークンとシークレット取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# GitHub passwords.json URL
PASSWORDS_URL = "https://api.github.com/repos/fujikongu/line-tarot-bot/contents/password_issuer/passwords.json"

# GitHub から passwords.json を取得
def get_passwords():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(PASSWORDS_URL, headers=headers)
    if response.status_code == 200:
        content = json.loads(response.json()["content"].encode('utf-8').decode('utf-8'))
        return json.loads(content)
    else:
        return []

# /callback エンドポイント
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# メッセージハンドラー
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    passwords = get_passwords()

    if text in passwords:
        passwords.remove(text)
        update_passwords(passwords)
        quick_reply_buttons = [
            QuickReplyButton(action=MessageAction(label="恋愛運", text="恋愛運")),
            QuickReplyButton(action=MessageAction(label="仕事運", text="仕事運")),
            QuickReplyButton(action=MessageAction(label="金運", text="金運")),
            QuickReplyButton(action=MessageAction(label="結婚", text="結婚")),
            QuickReplyButton(action=MessageAction(label="未来の恋愛", text="未来の恋愛")),
            QuickReplyButton(action=MessageAction(label="今日の運勢", text="今日の運勢"))
        ]
        reply_text = "✅パスワード認証成功！\nジャンルを選んでください。"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text, quick_reply=QuickReply(items=quick_reply_buttons))
        )
    else:
        reply_text = "❌パスワードを入力してください。"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )

# GitHub passwords.json を更新
def update_passwords(passwords):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(PASSWORDS_URL, headers=headers)
    if response.status_code == 200:
        sha = response.json()["sha"]
        updated_content = json.dumps(passwords, ensure_ascii=False, indent=4)
        data = {
            "message": "Update passwords.json",
            "content": updated_content.encode("utf-8").decode("utf-8"),
            "sha": sha
        }
        requests.put(PASSWORDS_URL, headers=headers, data=json.dumps(data))

# ★ 重要！外部公開ポートで listen
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
