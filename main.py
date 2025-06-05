import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai

app = Flask(__name__)

# 環境変数からトークン・シークレット・OpenAIキーを取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MEMBER_PASSWORD = os.getenv("MEMBER_PASSWORD", "123abc")  # 共通パスワード
AUTHORIZED_USERS_FILE = "authorized_users.txt"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
openai.api_key = OPENAI_API_KEY

# ファイルから許可ユーザーIDを読み込む
def load_authorized_users():
    if not os.path.exists(AUTHORIZED_USERS_FILE):
        return set()
    with open(AUTHORIZED_USERS_FILE, "r") as f:
        return set(line.strip() for line in f.readlines())

# ユーザーIDをファイルに保存
def authorize_user(user_id):
    with open(AUTHORIZED_USERS_FILE, "a") as f:
        f.write(user_id + "\n")

@app.route("/")
def home():
    return "LINE占いBotは稼働中です。"

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
    user_message = event.message.text.strip()
    user_id = event.source.user_id
    authorized_users = load_authorized_users()

    # パスワード入力処理
    if user_message.startswith("会員パス："):
        input_pass = user_message.replace("会員パス：", "").strip()
        if input_pass == MEMBER_PASSWORD:
            if user_id not in authorized_users:
                authorize_user(user_id)
            reply_text = "認証完了しました。占いを始められます。"
        else:
            reply_text = "パスワードが間違っています。"
    elif user_id not in authorized_users:
        reply_text = "このBotを利用するには、noteで公開されている『会員パス』を送信してください。例：会員パス：123abc"
    else:
        # 占い応答（OpenAI）
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "あなたは有能なタロット占い師です。"},
                {"role": "user", "content": user_message},
            ],
        )
        reply_text = response["choices"][0]["message"]["content"].strip()

    # 応答送信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    app.run()
