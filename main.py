from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
import os
import random
import openai

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["LINE_CHANNEL_SECRET"])
openai.api_key = os.environ["OPENAI_API_KEY"]

GENRES = ["恋愛運", "仕事運", "金運", "結婚・未来の恋愛", "今日の運勢"]

@app.route("/")
def index():
    return "OK"

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
    user_text = event.message.text

    if user_text in GENRES:
        tarot_result = generate_tarot_response(user_text)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=tarot_result)
        )
    else:
        quick_reply = QuickReply(
            items=[
                QuickReplyButton(action=MessageAction(label=genre, text=genre))
                for genre in GENRES
            ]
        )
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="ジャンルを選んでください：",
                quick_reply=quick_reply
            )
        )

def generate_tarot_response(genre):
    card = random.choice(["運命の輪", "太陽", "月", "塔", "恋人", "力"])
    prompt = f"タロットカード「{card}」が{genre}について意味することを詳しく教えてください。"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"占い結果の取得中にエラーが発生しました: {str(e)}"

if __name__ == "__main__":
    app.run()
