
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction
)

app = Flask(__name__)

line_bot_api = LineBotApi("YOUR_CHANNEL_ACCESS_TOKEN")
handler = WebhookHandler("YOUR_CHANNEL_SECRET")

authenticated_users = set()
correct_password = "mem1091"

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
    user_text = event.message.text.strip()

    if user_text.startswith("会員パス："):
        password = user_text.replace("会員パス：", "").strip()
        if password == correct_password:
            authenticated_users.add(user_id)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="認証完了しました。占いを始められます。")
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="パスワードが間違っています。")
            )
        return

    if user_text.lower() in ["占って", "占いして", "占う", "占い"]:
        if user_id not in authenticated_users:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="このBotを利用するには、noteで公開されている『会員パス』を送信してください。
例：会員パス：123abc"
                )
            )
            return

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="占いたい項目を教えてください。
例：「恋愛運」「金運」「仕事運」「結婚運」「今日の運勢」",
                quick_reply=QuickReply(items=[
                    QuickReplyButton(action=MessageAction(label="恋愛運", text="恋愛運")),
                    QuickReplyButton(action=MessageAction(label="金運", text="金運")),
                    QuickReplyButton(action=MessageAction(label="仕事運", text="仕事運")),
                    QuickReplyButton(action=MessageAction(label="結婚運", text="結婚運")),
                    QuickReplyButton(action=MessageAction(label="今日の運勢", text="今日の運勢")),
                ])
            )
        )
        return

    # 以下、ジャンルに応じた占い処理（仮）
    if user_id in authenticated_users and user_text in ["恋愛運", "金運", "仕事運", "結婚運", "今日の運勢"]:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"{user_text}についての占い結果を準備中です。")
        )
        return

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="メッセージを正しく入力してください。")
    )

if __name__ == "__main__":
    app.run()
