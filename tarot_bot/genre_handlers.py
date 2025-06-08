
# -*- coding: utf-8-sig -*-
import json
from linebot.models import TextSendMessage, QuickReply, QuickReplyButton, MessageAction

def send_genre_selection(event, line_bot_api):
    genres = ["恋愛運", "仕事運", "金運", "結婚", "今日の運勢"]
    quick_reply_buttons = [
        QuickReplyButton(action=MessageAction(label=genre, text=genre))
        for genre in genres
    ]
    message = TextSendMessage(
        text="✅パスワード認証成功！
ジャンルを選んでください。",
        quick_reply=QuickReply(items=quick_reply_buttons)
    )
    line_bot_api.reply_message(event.reply_token, message)

def send_tarot_reading(event, genre):
    message = TextSendMessage(text=f"🔮『{genre}』の占い結果はこちらです！（※テンプレート処理はまだ仮実装）")
    event.reply_token  # ここはline_bot_api呼び出し側で送信する実装
