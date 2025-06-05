
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
)

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = "HGXyasDnCBkCz6kJQkYUl1YmbBxWqlMGdOcPsqirW098MPJlS9oRCIlfbP6wPSqafFb9ng6NeFPOQKMKOIYPqhqjhB3oBjZXGgZq8UzMsW6v204VHRS1xgRkCWvFBRbWXsGphmAy3tJptzzkx79eqQdB0489/10/w1cDnyilFU="
LINE_CHANNEL_SECRET = "a0d8b83b274d45da4527bfee014097ef"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 会員パスワード
MEMBER_PASSWORD = "mem1091"

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

    # 認証待ち：パスワード入力の促し
    if user_text.lower() in ["start", "パス", "パスワード"]:
        reply = TextSendMessage(text="🔒 会員パスワードを入力してください（例：mem1091）")
        line_bot_api.reply_message(event.reply_token, reply)
        return

    # パスワード認証処理（「mem1091」または「会員パス：mem1091」形式）
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

    # 占い結果（簡易版）
    genre_messages = {
        "恋愛運": "💖 恋愛運：心ときめく出会いが近づいています。",
        "仕事運": "💼 仕事運：チャンスはあなたの準備次第です。",
        "金運": "💰 金運：予想外の収入に期待できそう！",
        "結婚・未来の恋愛": "💍 結婚・未来の恋愛：大きな転機が訪れそうです。",
        "今日の運勢": "🌟 今日の運勢：ポジティブな気持ちが幸運を呼びます。"
    }

    if user_text in genre_messages:
        reply = TextSendMessage(text=genre_messages[user_text])
    else:
        reply = TextSendMessage(text="このBotを利用するには、会員パスワードを入力してください。\n例：mem1091")

    line_bot_api.reply_message(event.reply_token, reply)

if __name__ == "__main__":
    app.run()
