
# genre_handlers.py

import json
import os
from linebot.models import TextSendMessage
from tarot_data import load_tarot_template

def handle_genre_selection(event, line_bot_api, PASSWORDS_URL, GITHUB_TOKEN, genre_file_map):
    user_id = event.source.user_id
    selected_genre = event.postback.data if hasattr(event, 'postback') else event.message.text.strip()

    print(f"[DEBUG] ジャンル選択を受信: {selected_genre}")

    if selected_genre not in genre_file_map:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ 無効なジャンルが選択されました。もう一度選んでください。")
        )
        return

    print(f"[DEBUG] テンプレート読み込み開始: {selected_genre}")
    template = load_tarot_template(selected_genre)
    if not template:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ 占いデータの読み込みに失敗しました。")
        )
        return

    # 占い結果メッセージ作成
    result_message = f"🔮【{selected_genre}】占い結果\n\n"
    for key, value in template.items():
        result_message += f"{key}: {value}\n\n"

    print(f"[DEBUG] 占い結果生成完了: {selected_genre}")
    print(f"[DEBUG] メッセージ送信実行")

    # 返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=result_message)
    )
