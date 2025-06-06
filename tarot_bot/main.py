
import os
import json
import requests
import base64
import random
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
)

app = Flask(__name__)

# 環境変数
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# GitHub passwords.json URL
PASSWORDS_URL = "https://api.github.com/repos/fujikongu/line-tarot-bot/contents/password_issuer/passwords.json"

# ユーザーステータス
user_states = {}

# パスワード取得
def get_passwords():
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }
    response = requests.get(PASSWORDS_URL, headers=headers)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        print(f"Failed to fetch passwords.json: {response.status_code}")
        return []

# パスワード更新
def update_passwords_json(new_passwords):
    url = PASSWORDS_URL
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    get_response = requests.get(url, headers=headers)
    sha = get_response.json()["sha"] if get_response.status_code == 200 else None
    encoded_content = base64.b64encode(json.dumps(new_passwords, ensure_ascii=False, indent=2).encode()).decode()
    data = {
        "message": "Update passwords.json",
        "content": encoded_content,
        "sha": sha
    }
    r = requests.put(url, headers=headers, json=data)
    if r.status_code not in [200, 201]:
        raise Exception(f"Failed to update passwords.json: {r.status_code}")

# 占いテンプレート取得
def load_tarot_templates():
    with open("tarot_templates_by_genre.json", "r", encoding="utf-8") as f:
        return json.load(f)

# /callback エンドポイント
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# メッセージ受信
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text.strip()
    state = user_states.get(user_id, {"stage": "password"})

    # パスワード認証
    if state["stage"] == "password":
        passwords = get_passwords()
        valid_passwords = [entry["password"] for entry in passwords if not entry.get("used", False)]
        if user_message in valid_passwords:
            # パスワード使用済みに更新
            for entry in passwords:
                if entry["password"] == user_message:
                    entry["used"] = True
                    break
            update_passwords_json(passwords)

            # 次のステージへ
            user_states[user_id] = {"stage": "genre_selection"}
            quick_reply = QuickReply(items=[
                QuickReplyButton(action=MessageAction(label=label, text=label))
                for label in ["恋愛運", "仕事運", "金運", "結婚・未来の恋愛", "今日の運勢"]
            ])
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="ジャンルを選んでください：", quick_reply=quick_reply)
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="パスワードを入力してください。（例：mem1091）")
            )

    # ジャンル選択
    elif state["stage"] == "genre_selection":
        genres = ["恋愛運", "仕事運", "金運", "結婚・未来の恋愛", "今日の運勢"]
        if user_message in genres:
            tarot_templates = load_tarot_templates()
            genre_templates = tarot_templates.get(user_message, [])
            selected_cards = random.sample(genre_templates, 5) if len(genre_templates) >= 5 else genre_templates

            result_text = "\n\n".join([
                f"{i+1}枚目: {card.get('card_name', '不明')}\n{card.get('message', '')}"
                for i, card in enumerate(selected_cards)
            ])

            ai_summary = "【AIまとめ（仮）】本日の運勢を前向きに楽しんでください！"

            line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text=f"【{user_message}】占い結果：\n\n{result_text}"),
                    TextSendMessage(text=ai_summary),
                    TextSendMessage(text="もう一度占うには新しいパスワードが必要です。")
                ]
            )
            user_states.pop(user_id, None)
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="無効なジャンルです。最初からやり直してください。")
            )
            user_states.pop(user_id, None)

# サーバー起動
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
