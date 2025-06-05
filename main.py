
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import os

app = Flask(__name__)

# 環境変数または直接記述（安全性のため環境変数推奨）
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "YOUR_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "YOUR_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

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

    if text.startswith("会員パス：") or text.startswith("会員パス:"):
        reply_text = "認証完了しました。占いを始められます。"
    elif text in ["占って", "占い", "占う"]:
        reply_text = "占いたい項目を教えてください。
例：「恋愛運」「金運」「仕事運」「結婚運」「今日の運勢」"
    elif text in ["恋愛運", "金運", "仕事運", "結婚運", "今日の運勢"]:
        reply_text = f"{text}の結果：近日中に素敵な出来事が訪れるかもしれません。"
    else:
        reply_text = "このBotを利用するには、note で公開されている『会員パス』を送信してください。
例：会員パス：123abc"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    app.run()
