import os
import json
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

from .genre_handlers import send_tarot_reading

app = Flask(__name__)

# 環境変数
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

PASSWORDS_URL = "https://api.github.com/repos/fujikongu/line-tarot-bot/contents/password_issuer/passwords.json"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3.raw"
}

# パスワード読み込み
def load_passwords():
    response = requests.get(PASSWORDS_URL, headers=HEADERS)
    if response.status_code == 200:
        print("[DEBUG] GitHub API status: 200")
        return json.loads(response.text)
    else:
        print(f"[DEBUG] GitHub API status: {response.status_code}")
        return []

# パスワード更新
def update_passwords(passwords):
    update_url = PASSWORDS_URL
    get_response = requests.get(update_url, headers=HEADERS)
    if get_response.status_code == 200:
        sha = get_response.json()["sha"]
    else:
        print(f"[ERROR] Failed to get SHA: {get_response.status_code}")
        return

    content = json.dumps(passwords, indent=4, ensure_ascii=False)
    encoded_content = content.encode("utf-8").decode("utf-8")
    data = {
        "message": "Update passwords.json",
        "content": encoded_content.encode("utf-8").decode("utf-8").encode("base64").decode("utf-8"),
        "sha": sha
    }

    put_response = requests.put(update_url, headers=HEADERS, data=json.dumps(data))
    print(f"[DEBUG] GitHub update status: {put_response.status_code}")

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
    print(f"[DEBUG] Received message: {user_message}")

    passwords = load_passwords()
    print(f"[DEBUG] Loaded passwords: {passwords}")

    if user_message.startswith("mem"):
        matched = False
        for entry in passwords:
            if entry["password"] == user_message:
                matched = True
                if not entry["used"]:
                    entry["used"] = True
                    update_passwords(passwords)
                    print("[DEBUG] Password matched → Sending genre selection")

                    quick_reply_buttons = [
                        QuickReplyButton(action=MessageAction(label="恋愛運", text="恋愛運")),
                        QuickReplyButton(action=MessageAction(label="仕事運", text="仕事運")),
                        QuickReplyButton(action=MessageAction(label="金運", text="金運")),
                        QuickReplyButton(action=MessageAction(label="結婚", text="結婚")),
                        QuickReplyButton(action=MessageAction(label="今日の運勢", text="今日の運勢"))
                    ]

                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="✅パスワード認証成功！\nジャンルを選んでください。",
                            quick_reply=QuickReply(items=quick_reply_buttons)
                        )
                    )
                else:
                    print("[DEBUG] Password already used → Inform user")
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="❌このパスワードはすでに使用済みです。\nご利用には新しいチケットをご購入ください。"
                        )
                    )
                break
        if not matched:
            print("[DEBUG] Password not matched → Asking again")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌パスワードを入力してください。")
            )
    elif user_message in ["恋愛運", "仕事運", "金運", "結婚", "今日の運勢"]:
        print(f"[DEBUG] Genre selected: {user_message} → Calling send_tarot_reading")
        send_tarot_reading(event, user_message)
    else:
        print("[DEBUG] Unrecognized input → Asking for password")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌パスワードを入力してください。")
        )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
