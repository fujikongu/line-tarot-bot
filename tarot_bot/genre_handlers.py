
from linebot import LineBotApi
from linebot.models import TextSendMessage
from tarot_data import tarot_templates

# main.py 側の LineBotApi インスタンスを使う
from main import line_bot_api

def handle_genre_selection(event, genre):
    user_id = event.source.user_id
    reply_token = event.reply_token

    # tarot_templates からジャンルのテンプレートを取得
    genre_template = tarot_templates.get(genre)

    if genre_template is None:
        line_bot_api.reply_message(reply_token, TextSendMessage(text="❌ 選択したジャンルのテンプレートが見つかりませんでした。"))
        return

    # 占い結果メッセージを作成
    result_text = f"🔮【{genre}の占い結果】🔮\n\n"
    for card_num, interpretation in genre_template.items():
        result_text += f"{card_num}: {interpretation}\n\n"

    # メッセージ送信
    line_bot_api.reply_message(reply_token, TextSendMessage(text=result_text))
