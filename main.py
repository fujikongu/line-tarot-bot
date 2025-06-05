from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
)

import os

app = Flask(__name__)

# 環境変数からLINEの設定を読み込む
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 会員パスワード（noteで共有するものと一致）
MEMBER_PASSWORD = "mem1091"

# ユーザー認証用の一時保存（簡易実装）
authorized_users = set()

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
    text = event.message.text.strip()

    if text.startswith("会員パス"):
        if MEMBER_PASSWORD in text:
            authorized_users.add(user_id)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="認証完了しました。占いを始められます。")
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="パスワードが間違っています。noteで公開されている『会員パス』をご確認ください。")
            )
        return

    if user_id not in authorized_users:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="このBotを利用するには、noteで公開されている『会員パス』を送信してください。
例：会員パス：123abc")
        )
        return

    if text in ["占って", "占い", "占いして"]:
        quick_reply = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="恋愛運", text="恋愛運")),
            QuickReplyButton(action=MessageAction(label="金運", text="金運")),
            QuickReplyButton(action=MessageAction(label="仕事運", text="仕事運")),
            QuickReplyButton(action=MessageAction(label="結婚運", text="結婚運")),
            QuickReplyButton(action=MessageAction(label="今日の運勢", text="今日の運勢"))
        ])
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="占いたい項目を教えてください。
例：「恋愛運」「金運」「仕事運」「結婚運」「今日の運勢」", quick_reply=quick_reply)
        )
        return

    # ジャンルに応じたタロット占い結果（ダミー）
    genre_responses = {
        "恋愛運": "あなたの恋愛運は好調です。積極的な行動が吉。",
        "金運": "無駄遣いに注意。貯金が鍵を握ります。",
        "仕事運": "努力が評価される時期です。挑戦を恐れずに。",
        "結婚運": "出会いの予感。結婚を意識する出来事があるかも。",
        "今日の運勢": "直感が冴える1日。迷ったら自分を信じて行動を。"
    }

    if text in genre_responses:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"{text}の結果：
{genre_responses[text]}")
        )
        return

    # その他の入力
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="メニューに従って操作してください。
「占って」と送ると、ジャンルが選べます。")
    )

if __name__ == "__main__":
    app.run()
