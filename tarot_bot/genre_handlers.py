
# genre_handlers.py

import json
import os
from linebot.models import TextSendMessage
from tarot_data import load_tarot_template  # 正しくこちらをimport

def handle_genre_selection(event, line_bot_api, PASSWORDS_URL, GITHUB_TOKEN, genre_file_map):
    user_id = event.source.user_id
    genre = event.postback.data if hasattr(event, 'postback') else event.message.text.strip()

    if genre not in genre_file_map:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ 無効なジャンルが選択されました。もう一度選んでください。")
        )
        return

    # tarotテンプレート読み込み
    template = load_tarot_template(genre_file_map[genre])
    if not template:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ 占いデータの読み込みに失敗しました。")
        )
        return

    # 占い結果のメッセージ整形
    result_message = f"🔮【{genre}】占い結果\n\n"
    for i, card in enumerate(template['cards'], 1):
        result_message += f"{i}枚目: {card['name']}（{card['position']}）\n意味: {card['meaning']}\n\n"

    result_message += f"\n💡 総合アドバイス:\n{template['advice']}"

    # 返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=result_message)
    )
