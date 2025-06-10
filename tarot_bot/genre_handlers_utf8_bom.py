
from linebot.models import QuickReply, QuickReplyButton, MessageAction
import tarot_data

# ジャンル選択後の処理
def handle_genre_selection(event, genre):
    tarot_texts = tarot_data.tarot_data.get(genre, [])

    if not tarot_texts:
        reply_text = "指定されたジャンルが見つかりませんでした。"
    else:
        # 5枚のカードを選択（とりあえず最初の5つを取得）
        selected_cards = tarot_texts[:5]
        reply_text = "\n\n".join(selected_cards)

    # ユーザーに送信するレスポンス
    return reply_text

# ジャンル選択用クイックリプライの生成
def create_genre_quick_reply():
    genres = list(tarot_data.tarot_data.keys())
    items = [
        QuickReplyButton(action=MessageAction(label=genre, text=genre))
        for genre in genres
    ]
    return QuickReply(items=items)
