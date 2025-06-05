from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, PostbackEvent, TemplateSendMessage, ButtonsTemplate, PostbackAction

app = Flask(__name__)

line_bot_api = LineBotApi('YOUR_CHANNEL_ACCESS_TOKEN')
handler = WebhookHandler('YOUR_CHANNEL_SECRET')

verified_users = set()
member_pass = "mem1091"

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
    text = event.message.text

    if user_id not in verified_users:
        if text.startswith("会員パス:"):
            input_pass = text.replace("会員パス:", "").strip()
            if input_pass == member_pass:
                verified_users.add(user_id)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="認証完了しました。占いを始められます。")
                )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="会員パスが違います。")
                )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="このBotを利用するには、noteで公開されている『会員パス』を送信してください。例: 会員パス: 123abc")
            )
    else:
        if text in ["占って", "占い"]:
            buttons_template = ButtonsTemplate(
                title="占いたい項目を選んでください",
                text="以下から選択してください",
                actions=[
                    PostbackAction(label="恋愛運", data="genre=love"),
                    PostbackAction(label="金運", data="genre=money"),
                    PostbackAction(label="仕事運", data="genre=work"),
                    PostbackAction(label="結婚運", data="genre=marriage"),
                    PostbackAction(label="今日の運勢", data="genre=today")
                ]
            )
            template_message = TemplateSendMessage(
                alt_text="占いたい項目を選んでください",
                template=buttons_template
            )
            line_bot_api.reply_message(event.reply_token, template_message)
        elif text in ["恋愛運", "金運", "仕事運", "結婚運", "今日の運勢"]:
            result = f"{text}の結果:ここに占い結果が表示されます。"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="「占って」または占いたいジャンルを入力してください。"))

if __name__ == "__main__":
    app.run()
