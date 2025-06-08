
import json
import random
from linebot.models import TextSendMessage

genre_to_filename = {
    "恋愛運": "romance_tarot_template.json",
    "仕事運": "work_tarot_template.json",
    "金運": "money_tarot_template.json",
    "結婚": "marriage_tarot_template.json",
    "今日の運勢": "daily_tarot_template.json"
}

def send_genre_selection(event, line_bot_api):
    from linebot.models import QuickReply, QuickReplyButton, MessageAction

    genres = list(genre_to_filename.keys())
    quick_reply_buttons = [
        QuickReplyButton(action=MessageAction(label=genre, text=genre))
        for genre in genres
    ]

    message = TextSendMessage(
        text="✅パスワード認証成功！\nジャンルを選んでください。",
        quick_reply=QuickReply(items=quick_reply_buttons)
    )
    line_bot_api.reply_message(event.reply_token, message)

def send_tarot_reading(event, genre, line_bot_api):
    try:
        template_file = genre_to_filename.get(genre)
        if not template_file:
            raise ValueError(f"Unsupported genre: {genre}")

        with open(template_file, 'r', encoding='utf-8-sig') as f:
            tarot_templates = json.load(f)

        cards = random.sample(list(tarot_templates.keys()), 5)

        messages = []
        for i, card in enumerate(cards, 1):
            card_data = tarot_templates[card]
            message_text = f"【{i}枚目】\nカード名：{card}\n意味：{card_data['meaning']}\n解説：{card_data['description']}"
            messages.append(TextSendMessage(text=message_text))

        line_bot_api.reply_message(event.reply_token, messages)

    except Exception as e:
        error_message = TextSendMessage(text=f"エラーが発生しました: {str(e)}")
        line_bot_api.reply_message(event.reply_token, error_message)
