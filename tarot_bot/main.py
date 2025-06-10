
import os
import json
import requests
import base64
import random
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction



app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

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

    # パスワード認証
    if "mem" in text:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="✅パスワード認証成功！ジャンルを選んでください。")
        )
        return

    # ジャンル選択 → 簡易返信例
    if text in ["恋愛運", "仕事運", "金運", "結婚", "今日の運勢"]:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"🔮{text} のタロット占い結果はこちら → (仮結果表示)")
        )
        return

    # その他メッセージ
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="🔹 パスワードを送信してください（例：memxxxx）")
    )

if __name__ == "__main__":
    app.run()
