
import json
import random
from linebot.models import TextSendMessage, QuickReply, QuickReplyButton, MessageAction

# ジャンル → JSON ファイル名マップ
GENRE_FILE_MAP = {
    "恋愛運": "romance_tarot_template.json",
    "仕事運": "work_tarot_template.json",
    "金運": "money_tarot_template.json",
    "結婚": "marriage_tarot_template.json",
    "未来の恋愛": "romance_tarot_template.json",
    "今日の運勢": "daily_tarot_template.json"
}

# ジャンル選択クイックリプライ送信
def send_genre_selection(event, line_bot_api):
    quick_reply_buttons = [
        QuickReplyButton(action=MessageAction(label=genre, text=genre))
        for genre in GENRE_FILE_MAP.keys()
    ]
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text="✅パスワード認証成功！ジャンルを選んでください。",
            quick_reply=QuickReply(items=quick_reply_buttons)
        )
    )

# 占い結果送信
def send_tarot_reading(event, line_bot_api, selected_genre):
    genre_file = GENRE_FILE_MAP.get(selected_genre)
    if not genre_file:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="エラー：ジャンルが見つかりませんでした。")
        )
        return

    try:
        with open(f"tarot_bot/{genre_file}", "r", encoding="utf-8") as f:
            tarot_template = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load {genre_file}: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="エラー：占いデータの読み込みに失敗しました。")
        )
        return

    # ランダムに5枚カード選択
    selected_cards = random.sample(tarot_template, 5)

    # 結果メッセージ構築
    result_message = f"🔮【{selected_genre}】占い結果🔮\n\n"
    for i, card in enumerate(selected_cards, 1):
        result_message += f"{i}. {card['name']} ({card['position']})\n→ {card['meaning']}\n\n"

    # LINE返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=result_message.strip())
    )
