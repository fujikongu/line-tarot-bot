
import os
import json
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

app = Flask(__name__)

# 環境変数からLINEチャネル情報とGitHubトークン取得
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = "fujikongu/line-tarot-bot"
GITHUB_FILE_PATH = "password_issuer/passwords.json"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ユーザーごとの認証状態保存
user_auth_status = {}

def fetch_passwords_from_github():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        print(f"Failed to fetch passwords.json: {response.status_code}, {response.text}")
        return []

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

    # ユーザー未認証かつパスワード入力の場面
    if user_auth_status.get(user_id) != "authenticated":
        passwords = fetch_passwords_from_github()
        if text in passwords:
            # パスワ有効
            user_auth_status[user_id] = "authenticated"

            # GitHub上のpasswords.jsonからこのパスを削除
            delete_password_from_github(text)

            # ジャンル選択を表示
            reply_genre_selection(event)
        else:
            # パスワ無効
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="有効なパスワードを入力してください。")
            )
    else:
        # 認証済ユーザー → 通常のジャンル選択後の会話進行（例として固定応答）
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"「{text}」の占い結果はこちら！（ここに占いロジックを追加）")
        )

def reply_genre_selection(event):
    quick_reply_buttons = [
        QuickReplyButton(action=MessageAction(label="恋愛運", text="恋愛運")),
        QuickReplyButton(action=MessageAction(label="仕事運", text="仕事運")),
        QuickReplyButton(action=MessageAction(label="金運", text="金運")),
        QuickReplyButton(action=MessageAction(label="結婚", text="結婚")),
        QuickReplyButton(action=MessageAction(label="未来の恋愛", text="未来の恋愛")),
        QuickReplyButton(action=MessageAction(label="今日の運勢", text="今日の運勢"))
    ]

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text="ジャンルを選んでください：",
            quick_reply=QuickReply(items=quick_reply_buttons)
        )
    )

def delete_password_from_github(used_password):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 最新ファイル取得
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch for delete: {response.status_code}, {response.text}")
        return

    data = response.json()
    sha = data["sha"] if "sha" in data else None
    content_json = json.loads(requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3.raw"}).text)

    # 使用済パス削除
    if used_password in content_json:
        content_json.remove(used_password)

    updated_content = json.dumps(content_json, ensure_ascii=False, indent=2)

    update_data = {
        "message": f"Remove used password {used_password}",
        "content": updated_content.encode("utf-8").decode("utf-8"),
        "sha": sha
    }

    put_response = requests.put(url, headers=headers, json=update_data)

    if put_response.status_code not in [200, 201]:
        print(f"Failed to update passwords.json: {put_response.status_code}, {put_response.text}")
    else:
        print(f"Password {used_password} removed successfully.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
