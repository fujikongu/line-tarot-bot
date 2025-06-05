
import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# LINE認証情報
LINE_CHANNEL_ACCESS_TOKEN = "HGXyasDnCBCKz6QJkQU1YiUmBXnlqVMGdc0PSqjrW098MPjSlo9RcllfbP6WPSqafB9gmg6NeFPOQKMkOlYPqhqjhB3oBjZXGzgz8UzMsW6v204VHRs1xggRkCwWFRbWsXGphmAy31ptxzzk79eaQdB048f9/1O/w1cDnIylIFU="
LINE_CHANNEL_SECRET = "a0dbb83b2744d5da4527bfee014097ef"

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
    user_msg = event.message.text.strip()
    if user_msg.startswith("会員パス") and "mem1091" in user_msg:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="認証完了しました。占いを始められます。")
        )
    elif user_msg in ["占って", "占い"]:
        buttons = ["恋愛運", "金運", "仕事運", "結婚運", "今日の運勢"]
        reply_text = "占いたい項目を教えてください。
例：" + "、".join([f"「{b}」" for b in buttons])
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
    elif user_msg in ["恋愛運", "金運", "仕事運", "結婚運", "今日の運勢"]:
        result = f"{user_msg}の結果：今のあなたに必要なメッセージが届いています。詳しくはカードを見てみましょう。"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=result)
        )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="このBotを利用するには、noteで公開されている『会員パス』を送信してください。
例：会員パス：123abc")
        )

if __name__ == "__main__":
    app.run()
