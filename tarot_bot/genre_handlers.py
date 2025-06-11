
import json
import random
from linebot import LineBotApi
from linebot.models import TextSendMessage

import os

# LINE BOT API 初期化
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# ジャンルごとのテンプレートファイルマップ
GENRE_FILE_MAP = {
    "恋愛運": "tarot_bot/romance_tarot_template.json",
    "仕事運": "tarot_bot/work_tarot_template.json",
    "金運": "tarot_bot/money_tarot_template.json",
    "結婚": "tarot_bot/marriage_tarot_template.json",
    "今日の運勢": "tarot_bot/daily_tarot_template.json",
}

# タロット占い送信関数
def send_tarot_reading(event, genre):
    print(f"[DEBUG] send_tarot_reading() called with genre: {genre}")

    file_path = GENRE_FILE_MAP.get(genre)
    if not file_path:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ジャンルデータが見つかりませんでした。")
        )
        return

    with open(file_path, "r", encoding="utf-8") as f:
        tarot_data = json.load(f)

    cards = random.sample(tarot_data["cards"], 5)

    result_text = f"🔮【{genre}】の占い結果\n\n"
    for i, card in enumerate(cards, 1):
        result_text += f"{i}. {card['name']} - {card['meaning']}\n\n"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=result_text)
    )
