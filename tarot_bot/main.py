import os
import json
import requests
import base64
import random
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

import genre_handlers
import tarot_data

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

PASSWORDS_URL = "https://api.github.com/repos/fujikongu/line-tarot-bot/contents/password_issuer/passwords.json"

user_state = {}

# GitHub から passwords.json を取得
def get_passwords():
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    response = requests.get(PASSWORDS_URL, headers=headers)
    if response.status_code == 200:
        content = response.json()
        file_content = base64.b64decode(content["content"]).decode("utf-8-sig")
        return json.loads(file_content)
    else:
        print("Error fetching passwords.json:", response.status_code)
        return {}

# GitHub へ passwords.json を更新
def update_passwords(passwords):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    get_response = requests.get(PASSWORDS_URL, headers=headers)
    if get_response.status_code == 200:
        sha = get_response.json()["sha"]
        updated_content = base64.b64encode(json.dumps(passwords, ensure_ascii=False, indent=4).encode("utf-8-sig")).decode("utf-8")
        data = {
            "message": "Update passwords.json",
            "content": updated_content,
            "sha": sha
        }
        put_response = requests.put(PASSWORDS_URL, headers=headers, data=json.dumps(data))
        if put_response.status_code not in [200, 201]:
            print("Error updating passwords.json:", put_response.status_code)
    else:
        print("Error getting current passwords.json SHA:", get_response.status_code)

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
    user_id = event.source.user_id
    text = event.message.text.strip()

    if user_id not in user_state:
        # パスワード認証フェーズ
        passwords = get_passwords()
        if passwords.get(text) == "unused":
            passwords[text] = "used"
            update_passwords(passwords)
            user_state[user_id] = {"state": "AWAITING_GENRE"}
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="✅ パスワード認証成功 🎉\nジャンルを選択してください：",
                    quick_reply=QuickReply(
                        items=[QuickReplyButton(action=MessageAction(label=genre, text=genre)) for genre in tarot_data.tarot_meanings.keys()]
                    )
                )
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌ パスワードが無効、または既に使用されています。")
            )
    else:
        # ジャンル選択後 → 診断フェーズ
        if user_state[user_id]["state"] == "AWAITING_GENRE":
            selected_genre = text
            if selected_genre in tarot_data.tarot_meanings:
                tarot_result = genre_handlers.get_tarot_reading(selected_genre)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=f"🔮【{selected_genre}】診断結果：\n\n{tarot_result}")
                )
                del user_state[user_id]
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="ジャンルが正しくありません。もう一度選択してください。")
                )

if __name__ == "__main__":
    app.run()
