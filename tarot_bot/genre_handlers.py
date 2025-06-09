
import tarot_data
from tarot_data import tarot_templates_by_genre
from linebot.models import TextSendMessage

def handle_genre_selection(event, line_bot_api):
    genre = event.message.text
    if genre in tarot_templates_by_genre:
        cards = tarot_data.draw_tarot_cards()
        result = tarot_data.format_tarot_result(genre, cards)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=result)
        )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="⚠️ 無効なジャンルが選択されました。")
        )
