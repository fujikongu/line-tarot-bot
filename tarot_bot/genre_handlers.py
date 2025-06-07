
import random

# ジャンルごとのタロットカード意味辞書
TAROT_TEMPLATES = {
    "恋愛運": {
        "THE_FOOL": "新しい出会い、自由な恋愛、冒険心",
        "THE_LOVERS": "恋愛成⻑、運命の出会い、愛の選択",
        "THE_TOWER": "突然の別れ、恋愛のトラブル"
    },
    "仕事運": {
        "THE_MAGICIAN": "新しいプロジェクトの成功、才能の発揮",
        "THE_EMPEROR": "リーダーシップの発揮、安定した地位",
        "THE_HERMIT": "一人でじっくり取り組む時期、内省の時間"
    },
    "金運": {
        "THE_WHEEL_OF_FORTUNE": "運気上昇、思わぬ収入",
        "THE_DEVIL": "浪費癖、借金に注意",
        "THE_STAR": "希望が見える、将来の投資に良い兆し"
    },
    "結婚": {
        "THE_LOVERS": "愛に満ちた結婚、理想的なパートナーシップ",
        "JUSTICE": "バランスの取れた結婚、契約や法的な進展",
        "DEATH": "関係の再スタート、変化の時期"
    },
    "今日の運勢": {
        "THE_STAR": "希望が見える良い一日",
        "THE_TOWER": "トラブルに注意する日",
        "THE_FOOL": "自由な発想で行動すると吉"
    }
}

def send_genre_selection(event, line_bot_api):
    quick_reply_buttons = [
        {
            "type": "action",
            "action": {"type": "message", "label": genre, "text": genre}
        }
        for genre in TAROT_TEMPLATES.keys()
    ]

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text="✅パスワード認証成功！ジャンルを選んでください。",
            quick_reply={
                "items": quick_reply_buttons
            }
        )
    )

def send_tarot_reading(event, genre, line_bot_api):
    if genre not in TAROT_TEMPLATES:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ 選択されたジャンルが存在しません。")
        )
        return

    cards = random.choices(list(TAROT_TEMPLATES[genre].keys()), k=5)

    reading_text = "🔮【{}のタロット占い】🔮\n\n".format(genre)
    for i, card in enumerate(cards, 1):
        meaning = TAROT_TEMPLATES[genre][card]
        reading_text += "■ {}枚目：{} → {}\n".format(i, card, meaning)

    reading_text += "\n✨総合アドバイス✨\n自分の気持ちを大切にし、流れに乗ることが成功のカギです。"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reading_text)
    )
