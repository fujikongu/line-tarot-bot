
def send_genre_selection(event, line_bot_api):
    reply_text = "✅パスワード認証成功！ジャンルを選んでください。"
    quick_reply_buttons = [
        {
            "type": "action",
            "action": {
                "type": "message",
                "label": "恋愛運",
                "text": "恋愛運"
            }
        },
        {
            "type": "action",
            "action": {
                "type": "message",
                "label": "仕事運",
                "text": "仕事運"
            }
        },
        {
            "type": "action",
            "action": {
                "type": "message",
                "label": "金運",
                "text": "金運"
            }
        },
        {
            "type": "action",
            "action": {
                "type": "message",
                "label": "結婚",
                "text": "結婚"
            }
        },
        {
            "type": "action",
            "action": {
                "type": "message",
                "label": "今日の運勢",
                "text": "今日の運勢"
            }
        }
    ]

    line_bot_api.reply_message(
        event.reply_token,
        {
            "type": "text",
            "text": reply_text,
            "quickReply": {
                "items": quick_reply_buttons
            }
        }
    )


def send_tarot_reading(event, genre):
    reply_text = f"🔮ジャンル「{genre}」の占い結果をお届けします。（ここに占い結果を表示）"

    return reply_text
