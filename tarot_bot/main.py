import json
import requests
from flask import Flask, request, abort

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import os

app = Flask(__name__)

# 環境変数からLINEのチャネルシークレットとアクセストークンを取得
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# GitHubのpasswords.jsonのRaw URL
PASSWORDS_JSON_URL = "https://raw.githubusercontent.com/fujikongu/line-tarot-bot/main/password_issuer/passwords.json"

# GitHubから最新のpasswords.jsonを取得
def fetch_valid_passwords():
    response = requests.get(PASSWORDS_JSON_URL)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to fetch passwords.json:", response.status_code)
        return []

# 占いの状態を記憶する辞書（ユーザーIDごと）
user_states = {}

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, MessageEvent.message.__class__)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text.strip()

    # 現在有効なパスワードを取得
    valid_passwords = fetch_valid_passwords()

    # ユーザーがまだ認証されていない場合
    if user_id not in user_states:
        if user_message in valid_passwords:
            user_states[user_id] = {'authenticated': True, 'used_password': user_message}
            # GitHub側のpasswords.jsonからこのパスワードは手動で消してください or 自動消去は別対応
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='パスワード認証成功！ジャンルを選んでください：\n1. 恋愛運\n2. 仕事運\n3. 金運\n4. 結婚\n5. 未来の恋愛\n6. 今日の運勢')
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='パスワードが正しくありません。')
            )
    else:
        # 認証済みの場合はジャンル選択受付中
        if user_message in ['1', '2', '3', '4', '5', '6']:
            genre_dict = {
                '1': '恋愛運',
                '2': '仕事運',
                '3': '金運',
                '4': '結婚',
                '5': '未来の恋愛',
                '6': '今日の運勢'
            }
            selected_genre = genre_dict[user_message]
            # 占い結果はダミー文
            result_text = f"【{selected_genre}】の占い結果：良い一日になるでしょう！"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=result_text)
            )
            # ユーザー状態リセット（1回のみ有効）
            del user_states[user_id]
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='ジャンルを1〜6の数字で選んでください。')
            )

@app.route("/", methods=['GET'])
def index():
    return "LINE Tarot Bot is running."

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
