
from linebot.models import TextSendMessage

# line_bot_api をインポートする
import os
from linebot import LineBotApi

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# send_tarot_reading 関数
def send_tarot_reading(event, genre):
    print(f"[DEBUG] send_tarot_reading called with genre: {genre}")
    
    # 仮の返信 → 本番はここにタロット結果を入れる
    result_text = f"【{genre}】のタロット結果はこちら → 仮の結果です。"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=result_text)
    )
