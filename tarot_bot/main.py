
import os
import json
import requests
import base64
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

# ✅ ジャンルハンドラ import 修正版
from genre_handlers import send_genre_selection, send_tarot_reading

app = Flask(__name__)

# LINE Botのチャネルアクセストークンとシークレット
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# GitHubのpasswords.jsonのURL
GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL")
PASSWORDS_JSON_URL = GITHUB_REPO_URL.replace("github.com", "api.github.com/repos") + "/contents/password_issuer/passwords.json"

# GitHubからpasswords.jsonを取得
def get_passwords_from_github():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(PASSWORDS_JSON_URL, headers=headers)
    print(f"GitHub API status: {r.status_code}")
    r.raise_for_status()
    content = r.json()["content"]
    decoded_content = base64.b64decode(content).decode("utf-8")
    passwords = json.loads(decoded_content)
    print(f"Loaded passwords: {passwords}")
    return passwords

# GitHubのpasswords.jsonを更新
def update_passwords_on_github(passwords):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    get_resp = requests.get(PASSWORDS_JSON_URL, headers=headers)
    get_resp.raise_for_status()
    sha = get_resp.json()["sha"]
    encoded_content = base64.b64encode(json.dumps(passwords, ensure_ascii=False, indent=2).encode("utf-8")).decode("utf-8")
    data = {
        "message": "Update password usage",
        "content": encoded_content,
        "sha": sha
    }
    put_resp = requests.put(PASSWORDS_JSON_URL, headers=headers, data=json.dumps(data))
    print(f"Update GitHub API status: {put_resp.status_code}")
    put_resp.raise_for_status()

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
    user_id = event.source.user_id
    user_message = event.message.text.strip()

    try:
        passwords = get_passwords_from_github()
    except Exception as e:
        print(f"[ERROR] Failed to fetch passwords.json: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="⚠️パスワード取得エラーが発生しました。しばらくしてからお試しください。")
        )
        return

    # 1️⃣ まず使用可能なパスワードを確認
    matched_password_entry = next((p for p in passwords if p["password"] == user_message), None)

    if matched_password_entry:
        if matched_password_entry["used"]:
            # 既に使用済み
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌このパスワードは既に使用されています。新しいパスワードをご購入ください。")
            )
        else:
            # 使用可能 → 使用済みに更新
            matched_password_entry["used"] = True
            try:
                update_passwords_on_github(passwords)
            except Exception as e:
                print(f"[ERROR] Failed to update passwords.json: {e}")
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="⚠️パスワード更新エラーが発生しました。しばらくしてからお試しください。")
                )
                return

            # 認証成功 → ジャンル選択へ
            send_genre_selection(event, line_bot_api)

    else:
        # パスワードでなければジャンル選択後の占いか通常メッセージ
        if user_message in ["恋愛運", "仕事運", "金運", "結婚", "未来の恋愛", "今日の運勢"]:
            send_tarot_reading(event, line_bot_api, user_message)
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌無効なパスワードです。")
            )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
