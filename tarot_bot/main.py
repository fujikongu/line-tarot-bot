
import os
import json
import requests
import base64
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
from genre_handlers import handle_genre_selection
from tarot_data import tarot_templates

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

PASSWORDS_URL = "https://api.github.com/repos/fujikongu/line-tarot-bot/contents/password_issuer/passwords.json"

user_states = {}

def get_passwords():
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    response = requests.get(PASSWORDS_URL, headers=headers)
    response.raise_for_status()
    return json.loads(response.text)

def update_passwords(passwords):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    get_response = requests.get(PASSWORDS_URL, headers=headers)
    get_response.raise_for_status()
    sha = get_response.json()["sha"]

    updated_content = base64.b64encode(json.dumps(passwords, ensure_ascii=False, indent=4).encode("utf-8")).decode("utf-8")

    data = {
        "message": "Update passwords.json",
        "content": updated_content,
        "sha": sha,
    }
    put_response = requests.put(PASSWORDS_URL, headers=headers, data=json.dumps(data))
    put_response.raise_for_status()

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature")
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

    # ジャンル選択中の場合
    if user_states.get(user_id) == "waiting_genre":
        handle_genre_selection(event, text)
        user_states[user_id] = None
        return

    passwords = get_passwords()
    for pw in passwords:
        if text == pw["password"] and not pw["used"]:
            pw["used"] = True
            update_passwords(passwords)
            user_states[user_id] = "waiting_genre"
            quick_reply = QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="恋愛運", text="恋愛運")),
                QuickReplyButton(action=MessageAction(label="仕事運", text="仕事運")),
                QuickReplyButton(action=MessageAction(label="金運", text="金運")),
                QuickReplyButton(action=MessageAction(label="結婚", text="結婚")),
                QuickReplyButton(action=MessageAction(label="今日の運勢", text="今日の運勢"))
            ])
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="✅パスワード認証成功！\nジャンルを選んでください。", quick_reply=quick_reply)
            )
            return

    # パスワード・ジャンル以外のメッセージはエラーメッセージ
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="❌パスワードが無効です。正しいパスワードを入力してください。")
    )

if __name__ == "__main__":
    app.run()
