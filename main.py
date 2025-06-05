
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

import os
import random

app = Flask(__name__)

YOUR_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
YOUR_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

AUTHORIZED_PASS = "mem1091"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

user_sessions = {}

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()

    if user_id not in user_sessions and not text.startswith("会員パス："):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="このBotを利用するには、noteで公開されている『会員パス』を送信してください。 例: 会員パス: 123abc")
        )
        return

    if text.startswith("会員パス：") or text.startswith("会員パス:"):
        password = text.split("：")[-1] if "：" in text else text.split(":")[-1]
        if password == AUTHORIZED_PASS:
            user_sessions[user_id] = True
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="認証完了しました。占いを始められます。")
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="会員パスが間違っています。")
            )
        return

    if text == "占って":
        quick_reply_buttons = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="恋愛運", text="恋愛運")),
            QuickReplyButton(action=MessageAction(label="金運", text="金運")),
            QuickReplyButton(action=MessageAction(label="仕事運", text="仕事運")),
            QuickReplyButton(action=MessageAction(label="結婚運", text="結婚運")),
            QuickReplyButton(action=MessageAction(label="今日の運勢", text="今日の運勢"))
        ])
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="占いたい項目を教えてください。", quick_reply=quick_reply_buttons)
        )
        return

    categories = {
        "恋愛運": ["今日は相手の気持ちがよく見える日。素直な態度が◎", "連絡のタイミングが鍵になる日。", "過去の恋にとらわれないで。"],
        "金運": ["無駄遣いに注意。財布のひもを締めると◎", "投資よりも節約を意識する日。", "臨時収入があるかも。"],
        "仕事運": ["集中力が高まりやすい。大きな仕事に◎", "トラブルに注意。慎重な判断が求められます。", "同僚との連携が鍵になる日。"],
        "結婚運": ["パートナーと将来について話すと良い日。", "価値観のすり合わせが大切。", "家庭的なことに目を向けて。"],
        "今日の運勢": ["今日はチャレンジ精神が大事。", "気分転換が幸運を呼びます。", "新しい出会いに恵まれるかも。"]
    }

    if text in categories:
        result = random.choice(categories[text])
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"{text}の結果:
{result}")
        )
        return

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="メニューから占いたいジャンルを選んでください。")
    )

if __name__ == "__main__":
    app.run()
