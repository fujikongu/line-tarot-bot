
import os
import json
import requests
import base64
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

import genre_handlers  # 修正版（正しいインポート）

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
def get_passwords():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(PASSWORDS_URL, headers=headers)
    if response.status_code == 200:
        content = response.json()
        file_content = base64.b64decode(content["content"]).decode("utf-8-sig")
        return json.loads(file_content), content["sha"]
    else:
        return [], None

# GitHub に passwords.json を更新
def update_passwords(passwords, sha):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    updated_content = json.dumps(passwords, ensure_ascii=False, indent=4)
    encoded_content = base64.b64encode(updated_content.encode("utf-8-sig")).decode("utf-8")
    data = {
        "message": "Update passwords.json",
        "content": encoded_content,
        "sha": sha
    }
    response = requests.put(PASSWORDS_URL, headers=headers, data=json.dumps(data))
    return response.status_code == 200 or response.status_code == 201

# パスワードを検証
def verify_password(input_password):
    passwords, sha = get_passwords()
    for pw in passwords:
        if pw["password"] == input_password:
            if pw["used"]:
                return "used", passwords, sha
            else:
                pw["used"] = True
                update_passwords(passwords, sha)
                return "valid", passwords, sha
    return "invalid", passwords, sha

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
    text = event.message.text.strip()

    # パスワード認証済みかどうかをユーザーごとに判定（簡易版）
    if not hasattr(handle_message, "verified_users"):
        handle_message.verified_users = set()

    user_id = event.source.user_id

    if user_id not in handle_message.verified_users:
        status, _, _ = verify_password(text)
        if status == "valid":
            handle_message.verified_users.add(user_id)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="✅パスワード認証成功！ジャンルを選んでください。",
                    quick_reply=QuickReply(items=[
                        QuickReplyButton(action=MessageAction(label=genre, text=genre))
                        for genre in ["恋愛運", "仕事運", "金運", "今日の運勢", "結婚", "未来の恋愛"]
                    ])
                )
            )
        elif status == "used":
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌このパスワードは既に使用されています。新しいパスワードをご購入ください。")
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌パスワードを入力してください。")
            )
    else:
        # 認証済みユーザー → ジャンルに応じた応答
        genre = text
        response_text = genre_handlers.get_tarot_reading(genre)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response_text)
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
