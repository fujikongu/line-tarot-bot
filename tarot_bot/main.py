
import os
import json
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 環境変数からキーを取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# GitHubのpasswords.jsonのURL
PASSWORDS_URL = "https://raw.githubusercontent.com/fujikongu/line-tarot-bot/main/password_issuer/passwords.json"

# 使用済みパスワードを記録する（メモリ保持の簡易版）
used_passwords = set()

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
    user_message = event.message.text.strip()

    # パスワード一覧をGitHubから取得
    try:
        import requests
        response = requests.get(PASSWORDS_URL)
        passwords = response.json()
    except Exception as e:
        print(f"Error loading passwords: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="エラーが発生しました。しばらくしてからお試しください。")
        )
        return

    # 認証チェック
    if user_message in passwords:
        if user_message in used_passwords:
            # すでに使用済み
            reply_text = "このパスワードはすでに使用されています。新しいパスワードを購入してください。"
        else:
            # 初回利用 → 使用済みに記録
            used_passwords.add(user_message)

            # ここに占い結果を返信（テスト版の固定メッセージ）
            reply_text = (
                "🎴 タロット占い結果 🎴\n\n"
                "1枚目：過去 → 太陽（正位置）\n"
                "2枚目：現在 → 月（逆位置）\n"
                "3枚目：未来 → 世界（正位置）\n"
                "4枚目：アドバイス → 星（正位置）\n"
                "5枚目：結果 → 力（正位置）\n\n"
                "✨ あなたの未来には明るい兆しが見えています。今は希望を持って進んでください！✨"
            )
    else:
        reply_text = "パスワードを入力してください。\n例 : mem1091"

    # 返信を送信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
