
from linebot import LineBotApi
from linebot.models import TextSendMessage, QuickReply, QuickReplyButton, MessageAction
import os

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))

def send_genre_selection(reply_token):
    message = TextSendMessage(
        text='占いたいジャンルを選んでください:',
        quick_reply=QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="恋愛運", text="恋愛運")),
            QuickReplyButton(action=MessageAction(label="仕事運", text="仕事運")),
            QuickReplyButton(action=MessageAction(label="金運", text="金運")),
            QuickReplyButton(action=MessageAction(label="今日の運勢", text="今日の運勢")),
            QuickReplyButton(action=MessageAction(label="結婚", text="結婚")),
            QuickReplyButton(action=MessageAction(label="未来の恋愛", text="未来の恋愛")),
        ])
    )
    line_bot_api.reply_message(reply_token, message)
