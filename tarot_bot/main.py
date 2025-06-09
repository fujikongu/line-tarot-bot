
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

def get_passwords():
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    response = requests.get(PASSWORDS_URL, headers=headers)
    response.raise_for_status()
    return json.loads(response.text)

def update_passwords(passwords):
    get_headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    get_response = requests.get(PASSWORDS_URL, headers=get_headers)
    get_response.raise_for_status()
    sha = get_response.json()["sha"]

    update_headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    update_data = {
        "message": "Update passwords.json",
        "content": base64.b64encode(json.dumps(passwords, ensure_ascii=False, indent=4).encode("utf-8")).decode("utf-8"),
        "sha": sha
    }
    put_response = requests.put(PASSWORDS_URL, headers=update_headers, json=update_data)
    put_response.raise_for_status()

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()
    user_id = event.source.user_id

    if user_message.startswith("mem"):
        passwords = get_passwords()
        matched_password = next((p for p in passwords if p["password"] == user_message), None)

        if matched_password:
            if matched_password["used"]:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="❌このパスワードは既に使用されています。新しいパスワードをご購入ください。")
                )
            else:
                matched_password["used"] = True
                update_passwords(passwords)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="✅パスワード認証成功！ジャンルを選んでください。",
                        quick_reply=QuickReply(items=[
                            QuickReplyButton(action=MessageAction(label="恋愛運", text="恋愛運")),
                            QuickReplyButton(action=MessageAction(label="仕事運", text="仕事運")),
                            QuickReplyButton(action=MessageAction(label="金運", text="金運")),
                            QuickReplyButton(action=MessageAction(label="結婚", text="結婚")),
                            QuickReplyButton(action=MessageAction(label="未来の恋愛", text="未来の恋愛")),
                            QuickReplyButton(action=MessageAction(label="今日の運勢", text="今日の運勢"))
                        ])
                    )
                )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌パスワードを入力してください。")
            )
    else:
        handle_genre_selection(event, user_id, user_message, line_bot_api)

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
