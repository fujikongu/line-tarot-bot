
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
)
import os
import random
import json

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = "HGXyasDnCBCkZ6QJKqXUi1YtmBxNqIvMGdc0PsqjrWO98MPjSIo9RcIlfbP6wPSqaFb9mg6NeFPOQKMKOIYPqhqjhB3oBjZXGgZq8UzMsW6v204VHRS1xggRkCwVFBRbWsXGphmAy31ptzxzk79eaQdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "a0d8b83b274d45da4527bfee014097ef"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

MEMBER_PASSWORD = "mem1091"

with open("romance_tarot_template.json", "r", encoding="utf-8") as f:
    tarot_dict = json.load(f)

positions = ["過去", "現在", "未来", "障害", "助言"]

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
    user_text = event.message.text.strip()

    if user_text.lower() in ["start", "パス", "パスワード"]:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(
            text="🔒 会員パスワードを入力してください（例：mem1091）"))
        return

    if user_text == MEMBER_PASSWORD or user_text in [f"会員パス：{MEMBER_PASSWORD}", f"会員パス:{MEMBER_PASSWORD}"]:
        reply = TextSendMessage(
            text="✅ 認証成功しました！占いたいジャンルを選んでください。",
            quick_reply=QuickReply(items=[
                QuickReplyButton(action=MessageAction(label="恋愛運", text="恋愛運")),
                QuickReplyButton(action=MessageAction(label="仕事運", text="仕事運")),
                QuickReplyButton(action=MessageAction(label="金運", text="金運")),
                QuickReplyButton(action=MessageAction(label="結婚・未来の恋愛", text="結婚・未来の恋愛")),
                QuickReplyButton(action=MessageAction(label="今日の運勢", text="今日の運勢")),
            ])
        )
        line_bot_api.reply_message(event.reply_token, reply)
        return

    if user_text == "恋愛運":
        drawn_cards = random.sample(list(tarot_dict.keys()), 5)
        results = []
        for i, card in enumerate(drawn_cards):
            position = positions[i]
            upright = random.choice(["正位置", "逆位置"])
            meaning = tarot_dict[card][upright][position]
            results.append(f"{i+1}枚目（{position}）: {meaning}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="🔮 恋愛運占い（5枚引き）結果：\n" + "\n\n".join(results)))
        return

    line_bot_api.reply_message(event.reply_token, TextSendMessage(
        text="このBotを利用するには、会員パスワードを入力してください。\n例：mem1091"))

if __name__ == "__main__":
    app.run()
