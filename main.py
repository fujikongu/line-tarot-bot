from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import random

app = Flask(__name__)

# 環境変数（RenderのDashboardで設定すること）
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# タロット占いの簡易結果サンプル（必要に応じて増やせます）
TAROT_READINGS = [
    "今日は新しい出会いがあるかもしれません。",
    "注意深く行動することで、トラブルを回避できます。",
    "あなたの決断が未来を切り開きます。",
    "無理せず、休むことも大切です。",
    "直感を信じて行動しましょう。"
]

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
    user_message = event.message.text
    if "占い" in user_message:
        result = random.choice(TAROT_READINGS)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"🔮タロット結果：{result}")
        )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="タロット占いをご希望ですか？「占い」と送ってください🔮")
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
