
import os
import json
import base64
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
from genre_handlers import genre_handlers

app = Flask(__name__)

# LINE Botのチャネルアクセストークンとシークレット
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# GitHubのpasswords.jsonのURL
PASSWORDS_URL = "https://api.github.com/repos/fujikongu/line-tarot-bot/contents/password_issuer/passwords.json"

def get_passwords():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(PASSWORDS_URL, headers=headers)
    if response.status_code == 200:
        content = response.json()["content"]
        decoded_content = base64.b64decode(content).decode('utf-8-sig')
        return json.loads(decoded_content)
    else:
        print(f"Failed to fetch passwords: {response.status_code}, {response.text}")
        return []

def update_passwords(passwords):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    get_response = requests.get(PASSWORDS_URL, headers=headers)
    sha = get_response.json()["sha"]
    updated_content = json.dumps(passwords, ensure_ascii=False, indent=4)
    encoded_content = base64.b64encode(updated_content.encode('utf-8-sig')).decode('utf-8')
    data = {
        "message": "Update passwords.json",
        "content": encoded_content,
        "sha": sha
    }
    response = requests.put(PASSWORDS_URL, headers=headers, json=data)
    if response.status_code not in [200, 201]:
        print(f"Failed to update passwords: {response.status_code}, {response.text}")

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()  # ← 追加！これで余分な空白対策

    passwords = get_passwords()

    # パスワード未入力時メッセージ
    if not user_message.startswith("mem"):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌パスワードを入力してください。")
        )
        return

    # パスワード判定
    password_entry = next((p for p in passwords if p["password"] == user_message), None)

    if password_entry:
        if password_entry["used"]:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌このパスワードは既に使用されています。新しいパスワードをご購入ください。")
            )
        else:
            password_entry["used"] = True
            update_passwords(passwords)
            quick_reply_buttons = [
                QuickReplyButton(action=MessageAction(label=genre, text=genre))
                for genre in genre_handlers.keys()
            ]
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="✅パスワード認証成功！ジャンルを選んでください。",
                    quick_reply=QuickReply(items=quick_reply_buttons)
                )
            )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌パスワードが無効です。正しいパスワードを入力してください。")
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
