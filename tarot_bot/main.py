
import os
import json
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
import genre_handlers

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

PASSWORDS_URL = "https://api.github.com/repos/fujikongu/line-tarot-bot/contents/password_issuer/passwords.json"

def get_passwords():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(PASSWORDS_URL, headers=headers)
    response.raise_for_status()
    content = response.json()["content"]
    return json.loads(requests.utils.unquote(response.json()["content"]).encode("utf-8").decode("utf-8"))

def update_passwords(passwords):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(PASSWORDS_URL, headers=headers)
    response.raise_for_status()
    sha = response.json()["sha"]
    updated_content = json.dumps(passwords, ensure_ascii=False, indent=2)
    b64_content = requests.utils.quote(updated_content.encode("utf-8"))
    data = {
        "message": "Update passwords.json",
        "content": b64_content,
        "sha": sha
    }
    response = requests.put(PASSWORDS_URL, headers=headers, json=data)
    response.raise_for_status()

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
    user_id = event.source.user_id
    user_message = event.message.text.strip()

    if user_message.startswith("mem"):
        passwords = get_passwords()
        for entry in passwords:
            if entry["password"] == user_message:
                if entry["used"]:
                    reply_message = "❌このパスワードは既に使用されています。新しいパスワードをご購入ください。"
                else:
                    entry["used"] = True
                    update_passwords(passwords)
                    reply_message = "✅パスワード認証成功！ジャンルを選んでください。"
                    send_genre_selection(event.reply_token)
                    return
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_message)
                )
                return

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌パスワードを入力してください。")
        )
    else:
        genre_handlers.handle_genre_selection(event, user_message)

def send_genre_selection(reply_token):
    items = ["恋愛運", "仕事運", "金運", "結婚", "未来の恋愛", "今日の運勢"]
    quick_reply_buttons = [
        QuickReplyButton(action=MessageAction(label=item, text=item))
        for item in items
    ]
    line_bot_api.reply_message(
        reply_token,
        TextSendMessage(
            text="ジャンルを選択してください：",
            quick_reply=QuickReply(items=quick_reply_buttons)
        )
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
