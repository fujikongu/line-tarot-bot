
import os
import json
import requests
import base64
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

from genre_handlers import handle_genre_selection

app = Flask(__name__)

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
        content = base64.b64decode(response.json()["content"]).decode("utf-8-sig")
        passwords = json.loads(content)
        print("✅ Loaded passwords:", passwords)  # ★ デバッグ用に追加
        return passwords
    else:
        print(f"❌ Failed to load passwords.json: {response.status_code} {response.text}")  # ★ デバッグ用に追加
        return []

@app.route("/webhook", methods=["POST"])
def webhook():
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
    user_id = event.source.user_id
    user_name = "User"  # ここは必要に応じて取得可能

    # パスワード認証
    passwords = get_passwords()
    matching_password = next((p for p in passwords if p["password"] == user_message and not p["used"]), None)

    if matching_password:
        # パスワード使用済みに更新
        matching_password["used"] = True

        # GitHubに更新をPUT
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        updated_content = base64.b64encode(json.dumps(passwords, ensure_ascii=False, indent=4).encode("utf-8-sig")).decode("utf-8")
        get_response = requests.get(PASSWORDS_URL, headers=headers)
        sha = get_response.json()["sha"]

        update_data = {
            "message": f"Mark password '{user_message}' as used by {user_name}",
            "content": updated_content,
            "sha": sha
        }

        put_response = requests.put(PASSWORDS_URL, headers=headers, data=json.dumps(update_data))
        print("✅ Password marked as used:", put_response.status_code)

        # ジャンル選択を表示
        reply_text = "✅ パスワード認証成功！
ジャンルを選んでください。"
        quick_reply = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="恋愛運", text="恋愛運")),
            QuickReplyButton(action=MessageAction(label="仕事運", text="仕事運")),
            QuickReplyButton(action=MessageAction(label="金運", text="金運")),
            QuickReplyButton(action=MessageAction(label="結婚", text="結婚")),
            QuickReplyButton(action=MessageAction(label="今日の運勢", text="今日の運勢")),
        ])
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text, quick_reply=quick_reply))

    else:
        # ジャンル選択が送られた場合は占い処理
        valid_genres = ["恋愛運", "仕事運", "金運", "結婚", "今日の運勢"]
        if user_message in valid_genres:
            handle_genre_selection(event, user_message)
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌パスワードが無効です。
正しいパスワードを入力してください。")
            )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
