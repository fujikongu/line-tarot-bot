
from tarot_data import tarot_templates

def handle_genre_selection(event, genre):
    user_id = event.source.user_id
    reply_token = event.reply_token

    # tarot_templates からジャンルのテンプレートを取得
    genre_template = tarot_templates.get(genre)

    if genre_template is None:
        return "選択されたジャンルは無効です。もう一度選んでください。"

    # タロットテンプレートから結果を組み立てる
    result_message = f"【{genre}】の占い結果：\n"
    for i, (card_num, interpretation) in enumerate(genre_template.items(), start=1):
        result_message += f"\n{i}枚目: {card_num} - {interpretation}\n"

    return result_message
