
import random
from linebot.models import TextSendMessage
from .genre_file_map import genre_file_map
from .main import line_bot_api

def send_tarot_reading(event, genre):
    tarot_template = genre_file_map.get(genre)
    if not tarot_template:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ジャンルデータが見つかりませんでした。")
        )
        return

    cards = random.sample(tarot_template["cards"], 5)
    result_text = f"🔮【{genre}の占い結果】🔮\n\n"
    for i, card in enumerate(cards, 1):
        result_text += f"{i}. {card['name']} - {card['meaning']}\n\n"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=result_text)
    )
