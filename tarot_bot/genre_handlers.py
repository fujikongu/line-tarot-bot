
import json
from linebot.models import TextSendMessage, QuickReply, QuickReplyButton, MessageAction

# クイックリプライ用ジャンル選択
def send_genre_selection(event, line_bot_api):
    quick_reply_buttons = [
        QuickReplyButton(action=MessageAction(label=genre, text=genre))
        for genre in ["恋愛運", "仕事運", "金運", "結婚", "未来の恋愛", "今日の運勢"]
    ]
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text="✅パスワード認証成功！ジャンルを選んでください。",
            quick_reply=QuickReply(items=quick_reply_buttons)
        )
    )

# タロット診断結果送信
def send_tarot_reading(event, line_bot_api, genre):
    try:
        with open("tarot_bot/tarot_templates_by_genre.json", "r", encoding="utf-8") as f:
            templates = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load tarot_templates_by_genre.json: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌診断テンプレートの読み込みに失敗しました。")
        )
        return

    if genre in templates:
        result_text = templates[genre]
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"🔮 {genre} の診断結果:\n\n{result_text}")
        )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌無効なジャンルが選択されました。")
        )
