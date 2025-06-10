
from flask import QuickReply, QuickReplyButton, MessageAction
from tarot_bot.tarot_data import tarot_data

def handle_genre_selection(event, line_bot_api, password_data):
    user_id = event.source.user_id
    genre = event.message.text.strip()

    # 有効なジャンルか確認
    if genre not in tarot_data:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ 無効なジャンルです。もう一度選んでください。")
        )
        return

    import random
    selected_cards = random.sample(list(tarot_data[genre].keys()), 5)

    messages = []
    for i, card in enumerate(selected_cards, start=1):
        meaning = tarot_data[genre][card]
        messages.append(f"【{i}枚目】{card}\n{meaning}")

    result_text = "\n\n".join(messages)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"🔮 {genre} の占い結果:\n\n{result_text}")
    )

    # パスワードを削除して1回限りにする
    if user_id in password_data:
        del password_data[user_id]
