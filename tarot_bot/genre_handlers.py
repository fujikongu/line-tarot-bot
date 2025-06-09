
import json
import os

def load_genre_file_map():
    with open("tarot_bot/genre_file_map.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_tarot_template(genre):
    genre_file_map = load_genre_file_map()
    if genre not in genre_file_map:
        raise ValueError(f"ジャンル '{genre}' は無効です。")

    template_file_path = os.path.join("tarot_bot", genre_file_map[genre])

    with open(template_file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def handle_genre_selection(genre):
    try:
        tarot_template = load_tarot_template(genre)

        # カードを5枚ランダムに選ぶ
        import random
        selected_cards = random.sample(tarot_template["cards"], 5)

        # メッセージ生成
        message = f"🔮【{genre}】の占い結果🔮\n\n"
        for idx, card in enumerate(selected_cards, start=1):
            message += f"{idx}. {card['name']} ({card['position']})\n{card['meaning']}\n\n"

        message += "✨あなたへの総合アドバイス✨\n"
        message += "（この部分は GPT API 呼び出しにより自動生成予定）"

        return message

    except Exception as e:
        return f"エラーが発生しました: {str(e)}"
