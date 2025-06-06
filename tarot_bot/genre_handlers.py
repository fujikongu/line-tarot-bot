import random

def get_tarot_response_by_genre(genre, client):
    cards = [
        "愚者", "魔術師", "女教皇", "女帝", "皇帝", "法王", "恋人", "戦車",
        "力", "隠者", "運命の輪", "正義", "吊るされた男", "死神", "節制", "悪魔",
        "塔", "星", "月", "太陽", "審判", "世界"
    ]
    selected_cards = random.sample(cards, 5)

    messages = [
        {"role": "system", "content": f"あなたは優れたタロット占い師です。ジャンル「{genre}」に関して、5枚のカードを深く読み解いて結果を出してください。"},
        {"role": "user", "content": f"引いたカードは {', '.join(selected_cards)} です。"}
    ]

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return response.choices[0].message.content.strip()
