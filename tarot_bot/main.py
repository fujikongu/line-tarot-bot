
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

PASSWORDS_URL = "https://api.github.com/repos/fujikongu/line-tarot-bot/contents/password_issuer/passwords.json"

user_states = {}

def get_passwords():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(PASSWORDS_URL, headers=headers)
    if response.status_code == 200:
        content = response.json()
        file_content = base64.b64decode(content["content"]).decode("utf-8")
        return json.loads(file_content)
    else:
        print("Error fetching passwords:", response.status_code, response.text)
        return {}

def update_passwords(passwords):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(PASSWORDS_URL, headers=headers)
    if response.status_code == 200:
        content = response.json()
        sha = content["sha"]
        updated_content = base64.b64encode(json.dumps(passwords, ensure_ascii=False, indent=4).encode("utf-8")).decode("utf-8")
        data = {
            "message": "Update passwords.json",
            "content": updated_content,
            "sha": sha
        }
        put_response = requests.put(PASSWORDS_URL, headers=headers, json=data)
        if put_response.status_code not in [200, 201]:
            print("Error updating passwords:", put_response.status_code, put_response.text)
    else:
        print("Error fetching current passwords for update:", response.status_code, response.text)

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

    if user_id not in user_states:
        user_states[user_id] = {"authenticated": False}

    state = user_states[user_id]

    if not state["authenticated"]:
        passwords = get_passwords()
        if text in passwords and passwords[text] == "valid":
            state["authenticated"] = True
            passwords[text] = "used"
            update_passwords(passwords)

            reply_text = "✅ パスワード認証に成功しました。\n占いたいジャンルを選んでください。"
            quick_reply = QuickReply(items=[
                QuickReplyButton(action=MessageAction(label=genre, text=genre))
                for genre in ["恋愛運", "仕事運", "金運", "結婚", "今日の運勢"]
            ])
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text, quick_reply=quick_reply)
            )
        else:
            reply_text = "❌ パスワードが無効です。正しいパスワードを入力してください。"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )
    else:
        handle_genre_selection(event, text)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
