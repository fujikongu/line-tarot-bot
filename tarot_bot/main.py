
import os
import json
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
from genre_handlers import genre_handlers

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ✅ ローカル passwords.json を直接読み込む
with open("password_issuer/passwords.json", "r", encoding="utf-8-sig") as f:
    passwords = json.load(f)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# ユーザーIDごとのセッション管理
user_sessions = {}

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()

    # セッション確認
    if user_id not in user_sessions:
        user_sessions[user_id] = {"authenticated": False}

    session = user_sessions[user_id]

    if not session["authenticated"]:
        # パスワード認証処理
        for entry in passwords:
            if entry["password"] == text:
                if entry["used"]:
                    reply_text = "❌このパスワードは既に使用されています。新しいパスワードをご購入ください。"
                else:
                    entry["used"] = True
                    session["authenticated"] = True
                    reply_text = "✅パスワード認証成功！ジャンルを選んでください。"

                    # passwords.json を更新
                    with open("password_issuer/passwords.json", "w", encoding="utf-8-sig") as f:
                        json.dump(passwords, f, ensure_ascii=False, indent=4)

                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
                return

        # パスワードが一致しなかった場合
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌パスワードを入力してください。"))
    else:
        # 認証後 → ジャンル選択
        if text in genre_handlers:
            genre_handlers[text](event, line_bot_api)
        else:
            quick_reply = QuickReply(items=[
                QuickReplyButton(action=MessageAction(label=genre, text=genre)) for genre in genre_handlers.keys()
            ])
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="ジャンルを選択してください。", quick_reply=quick_reply)
            )

# アプリ起動
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
