import os
import json
import requests
import base64
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
from genre_handlers import send_genre_selection, send_tarot_reading

app = Flask(__name__)

# 環境変数
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# GitHub passwords.json URL
PASSWORDS_JSON_URL = GITHUB_REPO_URL.replace("github.com", "api.github.com/repos") + "/contents/password_issuer/passwords.json"

# GitHub から passwords.json を取得
def get_passwords_from_github():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(PASSWORDS_JSON_URL, headers=headers)
    r.raise_for_status()
    content = r.json()["content"]
    decoded_content = base64.b64decode(content).decode("utf-8")
    return json.loads(decoded_content)

# GitHub に passwords.json を更新
def update_passwords_on_github(passwords):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(PASSWORDS_JSON_URL, headers=headers)
    r.raise_for_status()
    sha = r.json()["sha"]
    updated_content = base64.b64encode(json.dumps(passwords, ensure_ascii=False, indent=2).encode("utf-8")).decode("utf-8")
    data = {
        "message": "Update passwords.json",
        "content": updated_content,
        "sha": sha
    }
    update_url = PASSWORDS_JSON_URL
    r = requests.put(update_url, headers=headers, data=json.dumps(data))
    r.raise_for_status()

@app.route("/", methods=["GET"])
def index():
    return "LINE Tarot Bot is running."

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

    try:
        passwords = get_passwords_from_github()
    except Exception as e:
        print(f"[ERROR] Failed to fetch passwords.json: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="パスワード取得エラーが発生しました。しばらくしてからお試しください。")
        )
        return

    # パスワード認証フェーズ
    matching_password = next((p for p in passwords if p["password"] == user_message), None)
    if matching_password:
        if matching_password["used"]:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌このパスワードは既に使用されています。新しいパスワードをご購入ください。")
            )
        else:
            # パスワード初回認証成功 → ジャンル選択
            matching_password["used"] = True
            try:
                update_passwords_on_github(passwords)
            except Exception as e:
                print(f"[ERROR] Failed to update passwords.json: {e}")
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="パスワード状態の更新エラーが発生しました。")
                )
                return
            send_genre_selection(event.reply_token, line_bot_api)
    else:
        # ジャンル名か確認
        if user_message in ["恋愛運", "仕事運", "金運", "結婚", "未来の恋愛", "今日の運勢"]:
            send_tarot_reading(event.reply_token, user_message, line_bot_api)
        else:
            # 無効なパスワード
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌無効なパスワードです。")
            )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
