
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

# GitHubのpasswords.jsonの「RAW」URL（GITHUB_TOKEN不要版）
PASSWORDS_URL = "https://raw.githubusercontent.com/fujikongu/line-tarot-bot/main/password_issuer/passwords.json"

# ユーザーごとの状態管理
user_states = {}

def get_passwords():
    response = requests.get(PASSWORDS_URL)
    response.raise_for_status()
    return response.json()

def update_password_used(password_to_update):
    headers = {'Accept': 'application/vnd.github.v3+json'}
    # ここは今はGITHUB_TOKENなし → GitHub Actions等で運用する場合に改修予定
    print("⚠️ 手動でpasswords.json更新が必要です（現状はREADのみ）")

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
    user_id = event.source.user_id
    text = event.message.text.strip()

    state = user_states.get(user_id, "waiting_for_password")

    if state == "waiting_for_password":
        passwords = get_passwords()
        for entry in passwords:
            if entry["password"] == text:
                if entry["used"]:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="❌このパスワードは既に使用されています。 新しいパスワードをご購入ください。")
                    )
                    return
                else:
                    user_states[user_id] = "authenticated"
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="✅パスワード認証成功！ジャンルを選んでください。",
                            quick_reply=QuickReply(items=[
                                QuickReplyButton(action=MessageAction(label="恋愛運", text="恋愛運")),
                                QuickReplyButton(action=MessageAction(label="仕事運", text="仕事運")),
                                QuickReplyButton(action=MessageAction(label="金運", text="金運")),
                                QuickReplyButton(action=MessageAction(label="結婚", text="結婚")),
                                QuickReplyButton(action=MessageAction(label="未来の恋愛", text="未来の恋愛")),
                                QuickReplyButton(action=MessageAction(label="今日の運勢", text="今日の運勢"))
                            ])
                        )
                    )
                    # パスワードを使用済みに更新
                    entry["used"] = True
                    update_password_used(entry["password"])
                    return

        # パスワードが一致しない場合
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌パスワードを入力してください。")
        )

    elif state == "authenticated":
        handle_genre_selection(event, text)
        # 一度占いが完了したら状態をリセット（もう一度パスワード必須）
        user_states[user_id] = "waiting_for_password"

if __name__ == "__main__":
    app.run()
