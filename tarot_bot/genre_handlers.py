
from linebot.models import TextSendMessage, QuickReply, QuickReplyButton, MessageAction

def handle_genre_message(event, line_bot_api):
    # ジャンル選択用のQuickReplyを送信
    quick_reply_buttons = [
        QuickReplyButton(action=MessageAction(label="恋愛運", text="恋愛運")),
        QuickReplyButton(action=MessageAction(label="仕事運", text="仕事運")),
        QuickReplyButton(action=MessageAction(label="金運", text="金運")),
        QuickReplyButton(action=MessageAction(label="結婚", text="結婚")),
        QuickReplyButton(action=MessageAction(label="未来の恋愛", text="未来の恋愛")),
        QuickReplyButton(action=MessageAction(label="今日の運勢", text="今日の運勢")),
    ]

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text="占いたいジャンルを選んでください。",
            quick_reply=QuickReply(items=quick_reply_buttons)
        )
    )

def handle_genre_selection(event, line_bot_api):
    # ジャンル選択後の仮返信（ここに後で占い結果ロジックを入れる予定）
    genre = event.postback.data  # postback.data からジャンル取得
    user_id = event.source.user_id

    result_text = f"ジャンル「{genre}」の占い結果はこちら！（仮表示）"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=result_text)
    )
