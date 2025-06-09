
from linebot import LineBotApi
from linebot.models import TextSendMessage
from tarot_data import tarot_templates

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

GENRES = ["恋愛運", "仕事運", "金運", "結婚", "未来の恋愛", "今日の運勢"]

def handle_genre_selection(event, genre):
    if genre not in tarot_templates:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌無効なジャンルが選択されました。もう一度ジャンルを選んでください。")
        )
        return

    template = tarot_templates[genre]
    result_message = f"🔮【{genre}】の診断結果🔮\n\n"
    for i, (title, content) in enumerate(template.items(), start=1):
        result_message += f"{i}. {title}\n{content}\n\n"

    # 総合アドバイス部分は仮のメッセージでセット
    result_message += "⭐️【総合アドバイス】⭐️\n今は自分の気持ちを大切に行動していきましょう。"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=result_message)
    )
