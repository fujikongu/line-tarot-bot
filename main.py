import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai

app = Flask(__name__)

# 環境変数
YOUR_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
YOUR_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)
openai.api_key = OPENAI_API_KEY

# 会員パスワード
VALID_PASSWORD = "mem1091"
AUTHORIZED_USERS_FILE = "authorized_users.txt"

# 認証済みユーザー確認
def is_user_authorized(user_id):
    if not os.path.exists(AUTHORIZED_USERS_FILE):
        return False
    with open(AUTHORIZED_USERS_FILE, "r") as f:
        return user_id in f.read()

# 認証ユーザーを登録
def add_authorized_user(user_id):
    with open(AUTHORIZED_USERS_FILE, "a") as f:
        f.write(user_id + "\n")

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
    user_message = event.message.text.strip()

    if user_message.startswith("会員パス："):
        password = user_message.replace("会員パス：", "").strip()
        if password == VALID_PASSWORD:
            add_authorized_user(user_id)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="認証完了しました。占いを始められます。")
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="パスワードが正しくありません。")
            )
        return

    if not is_user_authorized(user_id):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="このBotを利用するには、noteで公開されている『会員パス』を送信してください。\n例：会員パス：123abc")
        )
        return

    if user_message in ["恋愛運", "金運", "仕事運", "結婚運", "今日の運勢"]:
        prompt = f"あなたは有能なタロット占い師です。ユーザーの「{user_message}」について、5枚引きで深く占い、結果を日本語で丁寧に説明してください。"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"{user_message}を占ってください"},
            ],
        )
        reply_text = response["choices"][0]["message"]["content"].strip()
    else:
        reply_text = "占いたい項目を教えてください。\n例：「恋愛運」「金運」「仕事運」「結婚運」「今日の運勢」"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    app.run()
