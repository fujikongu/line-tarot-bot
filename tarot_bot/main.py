
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
PASSWORDS_URL = "https://api.github.com/repos/fujikongu/line-tarot-bot/contents/password_issuer/passwords.json"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

user_states = {}

def get_passwords():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(PASSWORDS_URL, headers=headers)
    response.raise_for_status()
    content_encoded = response.json()["content"]
    content_json = base64.b64decode(content_encoded).decode("utf-8")
    print("DEBUG passwords content:", content_json)
    return json.loads(content_json)

def update_passwords(passwords):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    get_response = requests.get(PASSWORDS_URL, headers=headers)
    get_response.raise_for_status()
    sha = get_response.json()["sha"]

    update_response = requests.put(
        PASSWORDS_URL,
        headers=headers,
        data=json.dumps({
            "message": "Update passwords.json",
            "content": base64.b64encode(json.dumps(passwords, ensure_ascii=False, indent=4).encode("utf-8")).decode("utf-8"),
            "sha": sha
        })
    )
    update_response.raise_for_status()

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

    state = user_states.get(user_id, "awaiting_password")

    if state == "awaiting_password":
        passwords = get_passwords()
        for pw_entry in passwords:
            if pw_entry["password"] == text and not pw_entry["used"]:
                pw_entry["used"] = True
                update_passwords(passwords)
                user_states[user_id] = "waiting_genre"
                reply_text = "✅パスワード認証成功！\nジャンルを選んでください。"
                quick_reply = QuickReply(items=[
                    QuickReplyButton(action=MessageAction(label=label, text=label))
                    for label in ["恋愛運", "仕事運", "金運", "結婚", "今日の運勢"]
                ])
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text, quick_reply=quick_reply)
                )
                return
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌パスワードが無効です。正しいパスワードを入力してください。")
        )
    elif user_states.get(user_id) == "waiting_genre":
        selected_genre = text
        tarot_result = handle_genre_selection(selected_genre)

        # ユーザー状態を初期化
        user_states[user_id] = "idle"

        # tarot_result を返信
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=tarot_result)
        )

# アプリ起動
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
