
import os
from linebot.models import QuickReply, QuickReplyButton, MessageAction
from linebot.models import TextSendMessage

def handle_genre_selection(event, line_bot_api):
    genres = ["恋愛運", "仕事運", "金運", "結婚", "未来の恋愛", "今日の運勢"]

    quick_reply_buttons = [
        QuickReplyButton(action=MessageAction(label=genre, text=genre))
        for genre in genres
    ]

    message = "占いたいジャンルを選んでください："

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=message,
            quick_reply=QuickReply(items=quick_reply_buttons)
        )
    )
