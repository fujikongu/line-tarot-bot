
from linebot.models import TextSendMessage

def send_genre_selection(event):
    message = TextSendMessage(
        text="🔮ジャンルを選んでください。\n1️⃣ 恋愛運\n2️⃣ 仕事運\n3️⃣ 金運\n4️⃣ 結婚\n5️⃣ 今日の運勢"
    )
    return message

def send_tarot_reading(event, genre):
    if genre == "恋愛運":
        result = "💖 恋愛運の診断結果です..."
    elif genre == "仕事運":
        result = "💼 仕事運の診断結果です..."
    elif genre == "金運":
        result = "💰 金運の診断結果です..."
    elif genre == "結婚":
        result = "💍 結婚の診断結果です..."
    elif genre == "今日の運勢":
        result = "🌟 今日の運勢の診断結果です..."
    else:
        result = "⚠️ ジャンルが認識できませんでした。"

    return TextSendMessage(text=result)
