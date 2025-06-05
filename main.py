from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, MessageAction
import random
import os

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

valid_password = "mem1091"
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

    if user_id not in authorized_users:
        if text.startswith("会員パス：") or text.startswith("会員パス:"):
            password = text.split("：")[-1].strip() if "：" in text else text.split(":")[-1].strip()
            if password == valid_password:
                authorized_users.add(user_id)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="認証完了しました。占いを始められます。")
                )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="パスワードが間違っています。")
                )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="このBotを利用するには、note で公開されている『会員パス』を送信してください。
例：会員パス：123abc")
            )
        return

    if text in ["占って", "占い", "占ってください"]:
        buttons_template = ButtonsTemplate(
            title="占いたい項目を選んでください",
            text="以下から選択してください",
            actions=[
                MessageAction(label="恋愛運", text="恋愛運"),
                MessageAction(label="金運", text="金運"),
                MessageAction(label="仕事運", text="仕事運"),
                MessageAction(label="結婚運", text="結婚運"),
                MessageAction(label="今日の運勢", text="今日の運勢")
            ]
        )
        template_message = TemplateSendMessage(
            alt_text="占いたい項目を選んでください",
            template=buttons_template
        )
        line_bot_api.reply_message(event.reply_token, template_message)
    elif text in ["恋愛運", "金運", "仕事運", "結婚運", "今日の運勢"]:
        result = random.choice(["とても良い", "良い", "普通", "悪い", "最悪"])
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"{text}の結果:
{result}")
        )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="占いたい項目を教えてください。
例：「恋愛運」「金運」「仕事運」「結婚運」「今日の運勢」")
        )

if __name__ == "__main__":
    app.run()
