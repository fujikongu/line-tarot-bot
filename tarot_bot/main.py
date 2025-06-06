import os
import sys
import json
from flask import Flask, request, abort

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# 環境変数からトークンとシークレットを取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

if LINE_CHANNEL_ACCESS_TOKEN is None or LINE_CHANNEL_SECRET is None:
    print('環境変数が設定されていません。', file=sys.stderr)
    sys.exit(1)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Flaskアプリを作成
app = Flask(__name__)

# ルート確認用（GETでアクセスされた時）
@app.route("/", methods=['GET'])
def index():
    return "LINE Tarot Bot is running."

# LINE Webhook用のエンドポイント
@app.route("/callback", methods=['POST'])
def callback():
    # X-Line-Signature ヘッダー値を取得
    signature = request.headers['X-Line-Signature']

    # リクエストボディ（JSON形式）を取得
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# メッセージ受信時の処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    reply_message = f"あなたのメッセージ: {user_message}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_message)
    )

# アプリを起動
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
