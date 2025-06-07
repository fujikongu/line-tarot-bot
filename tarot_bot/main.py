
import os
import json
import requests
import base64
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

app = Flask(__name__)

# 環境変数
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL")

# LINE初期設定
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# GitHub passwords.json URL
PASSWORDS_JSON_URL = GITHUB_REPO_URL.replace("github.com", "api.github.com/repos") + "/contents/password_issuer/passwords.json"

# GitHubからpasswords.json取得
def get_passwords_from_github():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(PASSWORDS_JSON_URL, headers=headers)
    r.raise_for_status()
    content = r.json()["content"]
    decoded_content = base64.b64decode(content).decode("utf-8")
    return json.loads(decoded_content), r.json()["sha"]

# GitHubにpasswords.json更新
def update_passwords_to_github(passwords, sha):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    updated_content = base64.b64encode(json.dumps(passwords, ensure_ascii=False, indent=2).encode("utf-8")).decode("utf-8")
    data = {
        "message": "Update passwords.json (mark used)",
        "content": updated_content,
        "sha": sha
    }
    r = requests.put(PASSWORDS_JSON_URL, headers=headers, data=json.dumps(data))
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
        passwords_data, sha = get_passwords_from_github()
    except Exception as e:
        print(f"[ERROR] Failed to fetch passwords.json: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="パスワード取得エラーが発生しました。しばらくしてからお試しください。")
        )
        return

    # パスワード確認
    for pw_entry in passwords_data:
        if pw_entry["password"] == user_message:
            if not pw_entry["used"]:
                # 認証成功 → used: trueにして更新
                pw_entry["used"] = True
                try:
                    update_passwords_to_github(passwords_data, sha)
                except Exception as e:
                    print(f"[ERROR] Failed to update passwords.json: {e}")
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="パスワード更新エラーが発生しました。")
                    )
                    return

                # クイックリプライ送信
                quick_reply_buttons = [
                    QuickReplyButton(action=MessageAction(label=genre, text=genre))
                    for genre in ["恋愛運", "仕事運", "金運", "結婚", "未来の恋愛", "今日の運勢"]
                ]
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="✅パスワード認証成功！ジャンルを選んでください。",
                        quick_reply=QuickReply(items=quick_reply_buttons)
                    )
                )
                return
            else:
                # 既にused:trueの場合
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="❌このパスワードは既に使用されています。新しいパスワードをご購入ください。")
                )
                return

    # どのパスワードにも一致しない場合
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="❌無効なパスワードです。")
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
