
import os
import json
import requests
import base64
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

PASSWORDS_URL = "https://api.github.com/repos/fujikongu/line-tarot-bot/contents/password_issuer/passwords.json"

def get_passwords():
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    response = requests.get(PASSWORDS_URL, headers=headers)
    if response.status_code == 200:
        passwords = json.loads(response.text)
        print(f"DEBUG passwords.json content: {passwords}")  # ★DEBUG
        return passwords
    else:
        print(f"Failed to fetch passwords.json: {response.status_code}, {response.text}")
        return []

def update_passwords(passwords):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    get_response = requests.get(PASSWORDS_URL, headers=headers)
    sha = get_response.json()["sha"]
    updated_content = base64.b64encode(json.dumps(passwords, ensure_ascii=False, indent=4).encode("utf-8-sig")).decode("utf-8")

    data = {
        "message": "Update passwords.json",
        "content": updated_content,
        "sha": sha
    }

    put_response = requests.put(PASSWORDS_URL, headers=headers, data=json.dumps(data))
    if put_response.status_code not in [200, 201]:
        print(f"Failed to update passwords.json: {put_response.status_code}, {put_response.text}")

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
    print(f"DEBUG user_message: '{user_message}'")  # ★DEBUG

    passwords = get_passwords()
    password_data = next((p for p in passwords if p.get("password") == user_message), None)
    print(f"DEBUG matched password_data: {password_data}")  # ★DEBUG

    if password_data is not None and password_data.get("used", False) is False:
        # 認証成功 → 使用済に更新
        password_data["used"] = True
        update_passwords(passwords)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="✅パスワード認証成功！\nジャンルを選んでください。",
                quick_reply=QuickReply(items=[
                    QuickReplyButton(action=MessageAction(label="恋愛運", text="恋愛運")),
                    QuickReplyButton(action=MessageAction(label="仕事運", text="仕事運")),
                    QuickReplyButton(action=MessageAction(label="金運", text="金運")),
                    QuickReplyButton(action=MessageAction(label="結婚", text="結婚")),
                    QuickReplyButton(action=MessageAction(label="未来の恋愛", text="未来の恋愛")),
                    QuickReplyButton(action=MessageAction(label="今日の運勢", text="今日の運勢")),
                ])
            )
        )
    elif password_data is not None and password_data.get("used", False) is True:
        # 既に使用済
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌このパスワードは既に使用されています。新しいパスワードをご購入ください。")
        )
    else:
        # 認証失敗
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌パスワードを入力してください。")
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
