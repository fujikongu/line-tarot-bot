from linebot.models import TextSendMessage

def send_tarot_reading(event, genre):
    # 仮の診断結果
    result_text = f"🔮ジャンル「{genre}」の診断結果です。
あなたにとって良い日になりますように！"

    from main import line_bot_api
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=result_text)
    )