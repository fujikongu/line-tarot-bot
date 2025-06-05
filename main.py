
import os
import json
import random
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# ジャンルとテンプレートファイル名のマップ
GENRE_FILE_MAP = {
    "恋愛運": "romance_tarot_template.json",
    "仕事運": "work_tarot_template.json",
    "金運": "money_tarot_template.json",
    "結婚・未来の恋愛": "marriage_tarot_template.json",
    "今日の運勢": "daily_tarot_template.json"
}

VALID_PASSWORD = "mem1091"
SESSION_USERS = set()

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
    msg = event.message.text.strip()

    if user_id not in SESSION_USERS:
        if msg == VALID_PASSWORD:
            SESSION_USERS.add(user_id)
            quick_reply = QuickReply(items=[
                QuickReplyButton(action=MessageAction(label=genre, text=genre))
                for genre in GENRE_FILE_MAP.keys()
            ])
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="ジャンルを選んでください：", quick_reply=quick_reply)
            )
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="パスワードを入力してください。"))
    else:
        if msg not in GENRE_FILE_MAP:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="無効なジャンルです。最初からやり直してください。"))
            SESSION_USERS.discard(user_id)
            return

        file_name = GENRE_FILE_MAP[msg]
        try:
            with open(file_name, encoding="utf-8") as f:
                tarot_data = json.load(f)
        except FileNotFoundError:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="テンプレートが見つかりませんでした。"))
            return

        cards = random.sample(list(tarot_data.keys()), 5)
        positions = ["過去", "現在", "未来", "障害", "助言"]
        result_lines = []

        for i in range(5):
            card = cards[i]
            position = positions[i]
            upright = random.choice(["正位置", "逆位置"])
            meaning = tarot_data[card][upright][position]
            result_lines.append(f"{i+1}. {meaning}")

        # 正しいトリプルクォートによる結論文
        conclusion = """【結論】
あなたの状況は多面的であり、過去・現在・未来・障害・助言それぞれの要素が複雑に絡み合っています。
これらのカードは、あなたが今後どのような意識を持って行動すべきかを示しています。
最も重要なのは、助言にあった通り、自分自身の内面と丁寧に向き合いながら、前向きな行動を心がけることです。
すべてはあなたの選択と意志によって変わっていく可能性があります。"""

        full_message = "\n".join(result_lines) + "\n\n" + conclusion
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=full_message))
        SESSION_USERS.discard(user_id)

if __name__ == "__main__":
    app.run()
