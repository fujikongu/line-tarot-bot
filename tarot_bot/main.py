
# main.py

import os
import json
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from genre_handlers import handle_genre_selection

app = Flask(__name__)

# LINE Botのチャネルアクセストークンとシークレット
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PASSWORDS_URL = "https://api.github.com/repos/fujikongu/line-tarot-bot/contents/password_issuer/passwords.json"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# genre_file_map.json 読み込み
def load_genre_file_map():
    with open("tarot_bot/genre_file_map.json", "r", encoding="utf-8") as f:
        return json.load(f)

genre_file_map = load_genre_file_map()

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

    # パスワード認証部分はここに入る（省略）

    # ジャンル選択とみなして handle_genre_selection を呼び出す
    handle_genre_selection(
        event,
        line_bot_api,
        PASSWORDS_URL,
        GITHUB_TOKEN,
        genre_file_map
    )

if __name__ == "__main__":
    app.run()
