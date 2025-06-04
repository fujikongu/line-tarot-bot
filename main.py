import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
from genre_handlers import get_tarot_response_by_genre
from openai import OpenAI

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
    text = event.message.text
    genre_list = ["恋愛運", "仕事運", "金運", "結婚・未来の恋愛", "今日の運勢"]

    if text in genre_list:
        reply = get_tarot_response_by_genre(text, client)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
    else:
        quick_reply_buttons = [QuickReplyButton(action=MessageAction(label=g, text=g)) for g in genre_list]
        message = TextSendMessage(
            text="ジャンルを選んでください：",
            quick_reply=QuickReply(items=quick_reply_buttons)
        )
        line_bot_api.reply_message(event.reply_token, message)

if __name__ == "__main__":
    app.run()