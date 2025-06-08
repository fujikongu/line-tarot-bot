
import os
import json
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
from genre_handlers import handle_genre_message

app = Flask(__name__)

# LINE Botのチャネルアクセストークンとシークレット
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# GitHubのpasswords.jsonのURL
PASSWORDS_URL = "https://api.github.com/repos/fujikongu/line-tarot-bot/contents/password_issuer/passwords.json"

# GitHubからpasswords.jsonを取得
def get_passwords():
    headers = {}
    response = requests.get(PASSWORDS_URL, headers=headers)
    response.raise_for_status()
    content = response.json()["content"]
    decoded_content = requests.utils.unquote(content)
    passwords = json.loads(base64.b64decode(decoded_content).decode("utf-8-sig"))
    return passwords

# ユーザーのパスワード使用状況を記録
used_passwords = set()

# ユーザーごとの状態管理
user_states = {}

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

    if user_id not in user_states:
        user_states[user_id] = {"authenticated": False}

    state = user_states[user_id]

    if not state["authenticated"]:
        try:
            passwords = get_passwords()
        except Exception as e:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="⚠️ パスワードデータの取得に失敗しました。")
            )
            return

        matching_password = next((p for p in passwords if p["password"] == text and not p["used"]), None)

        if matching_password:
            state["authenticated"] = True
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="✅パスワード認証成功！ジャンルを選んでください。",
                    quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(action=MessageAction(label=label, text=label))
                            for label in ["恋愛運", "仕事運", "金運", "結婚", "未来の恋愛", "今日の運勢"]
                        ]
                    )
                )
            )
            # ※ GitHub側へのused更新はパスワード発行側が管理
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌パスワードを入力してください。")
            )
    else:
        handle_genre_message(event, user_id, text)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
