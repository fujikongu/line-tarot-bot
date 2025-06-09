
import os
import json
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
from genre_handlers import handle_genre_selection

app = Flask(__name__)

# LINE Botのチャネルアクセストークンとシークレット
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# GitHubのpasswords.jsonのURL
PASSWORDS_URL = "https://api.github.com/repos/fujikongu/line-tarot-bot/contents/password_issuer/passwords.json"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# GitHubからpasswords.jsonを取得
def get_passwords():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(PASSWORDS_URL, headers=headers)
    if response.status_code == 200:
        content = json.loads(response.json()["content"])
        return json.loads(base64.b64decode(content).decode("utf-8"))
    else:
        print(f"Failed to fetch passwords.json: {response.status_code}")
        return []

@app.route("/webhook", methods=["POST"])
def webhook():
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
    
    # 現在のユーザーステートを管理
    if not hasattr(app, "user_states"):
        app.user_states = {}
    state = app.user_states.get(user_id, {"stage": "password"})

    if state["stage"] == "password":
        passwords = get_passwords()
        matched = False
        for entry in passwords:
            if entry["password"] == text and not entry.get("used", False):
                matched = True
                entry["used"] = True  # ここではGitHubには保存しない簡易実装
                app.user_states[user_id] = {"stage": "genre_selection"}
                reply_text = "✅パスワード認証成功！ジャンルを選んでください。"
                quick_reply = QuickReply(items=[
                    QuickReplyButton(action=MessageAction(label=genre, text=genre))
                    for genre in ["恋愛運", "仕事運", "金運", "結婚", "今日の運勢"]
                ])
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text, quick_reply=quick_reply)
                )
                break

        if not matched:
            reply_text = "❌パスワードが無効です。正しいパスワードを入力してください。"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )

    elif state["stage"] == "genre_selection":
        genre = text
        handle_genre_selection(event, genre)
        # ステージをリセットして次回またパスワードから開始
        app.user_states[user_id] = {"stage": "password"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
