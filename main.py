from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, MessageAction

import random

app = Flask(__name__)

line_bot_api = LineBotApi('YOUR_CHANNEL_ACCESS_TOKEN')
handler = WebhookHandler('YOUR_CHANNEL_SECRET')

AUTHORIZED_PASSWORD = "mem1091"
AUTHORIZED_USERS = set()

TAROT_GENRES = ["恋愛運", "金運", "仕事運", "結婚運", "今日の運勢"]
TAROT_RESULTS = [
    "新たな展開が期待できます。",
    "注意が必要な時期です。",
    "思いがけないチャンスが訪れます。",
    "感情のバランスが重要です。",
    "自分を信じて進みましょう。"
]

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()

    if user_id not in AUTHORIZED_USERS:
        if text == f"会員パス：{AUTHORIZED_PASSWORD}":
            AUTHORIZED_USERS.add(user_id)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="認証完了しました。占いを始められます。")
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="このBotを利用するには、note で公開されている『会員パス』を送信してください。\n例：会員パス：123abc")
            )
        return

    if text in TAROT_GENRES:
        result = random.choice(TAROT_RESULTS)
        reply = f"{text}の結果：{result}"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply)
        )
    elif text in ["占って", "占い", "うらない"]:
        buttons_template = ButtonsTemplate(
            title="占いたい項目を選んでください",
            text="例：「恋愛運」「金運」「仕事運」「結婚運」「今日の運勢」",
            actions=[MessageAction(label=genre, text=genre) for genre in TAROT_GENRES]
        )
        template_message = TemplateSendMessage(
            alt_text="占いたい項目を選んでください",
            template=buttons_template
        )
        line_bot_api.reply_message(
            event.reply_token,
            template_message
        )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="「占って」と送信するとジャンルを選べます。")
        )

if __name__ == "__main__":
    app.run()