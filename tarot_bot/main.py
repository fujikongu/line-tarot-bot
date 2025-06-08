
import os
import json
import requests
import base64
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

app = Flask(__name__)

# LINE Botのチャネルアクセストークンとシークレット
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# GitHubのpasswords.jsonのURL
PASSWORDS_URL = "https://api.github.com/repos/fujikongu/line-tarot-bot/contents/password_issuer/passwords.json"

def get_passwords_from_github():
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    response = requests.get(PASSWORDS_URL, headers=headers)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        print(f"Failed to fetch passwords.json: {response.status_code}, {response.text}")
        return []

def update_passwords_on_github(passwords):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    get_response = requests.get(PASSWORDS_URL, headers=headers)
    sha = get_response.json()["sha"]
    updated_content = base64.b64encode(json.dumps(passwords, ensure_ascii=False, indent=4).encode("utf-8-sig")).decode("utf-8")

    data = {
        "message": "Update passwords.json",
        "content": updated_content,
        "sha": sha
    }

    put_response = requests.put(PASSWORDS_URL, headers=headers, data=json.dumps(data))
    if put_response.status_code not in [200, 201]:
        print(f"Failed to update passwords.json: {put_response.status_code}, {put_response.text}")

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

    # パスワード判定
    passwords = get_passwords_from_github()
    password_entry = next((p for p in passwords if p.get("password") == user_message), None)

    if password_entry:
        if password_entry.get("used"):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌このパスワードは既に使用されています。新しいパスワードをご購入ください。")
            )
            return

        password_entry["used"] = True
        update_passwords_on_github(passwords)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="✅パスワード認証成功！\nジャンルを選んでください。",
                quick_reply=QuickReply(items=[
                    QuickReplyButton(action=MessageAction(label="恋愛運", text="恋愛運")),
                    QuickReplyButton(action=MessageAction(label="仕事運", text="仕事運")),
                    QuickReplyButton(action=MessageAction(label="金運", text="金運")),
                    QuickReplyButton(action=MessageAction(label="結婚", text="結婚")),
                    QuickReplyButton(action=MessageAction(label="未来の恋愛", text="未来の恋愛")),
                    QuickReplyButton(action=MessageAction(label="今日の運勢", text="今日の運勢")),
                ])
            )
        )
        return

    # ここは占いジャンルの判定 (簡易版、詳細は genre_handlers.py 側で処理)
    valid_genres = ["恋愛運", "仕事運", "金運", "結婚", "未来の恋愛", "今日の運勢"]
    if user_message in valid_genres:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"「{user_message}」の占い結果を準備中です...")
        )
        return

    # それ以外のメッセージ
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="❌パスワードを入力してください。")
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
