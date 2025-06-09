
from linebot.models import TextSendMessage
from tarot_data import tarot_templates
import random

def handle_genre_selection(user_id, genre):
    # ジャンルが tarot_templates に存在するかチェック
    if genre not in tarot_templates:
        return TextSendMessage(text="⚠️ 無効なジャンルが選択されました。もう一度ジャンルを選んでください。")

    # ジャンルのカードリストから5枚ランダムに選択
    selected_cards = random.sample(tarot_templates[genre], 5)

    # 結果メッセージ生成
    result_message = f"🔮【{genre}の占い結果】🔮\n\n"
    for idx, card in enumerate(selected_cards, start=1):
        result_message += f"{idx}. {card}\n"

    result_message += "\n✨ご利用ありがとうございました✨"

    # LINEへ返却用メッセージ
    return TextSendMessage(text=result_message)
