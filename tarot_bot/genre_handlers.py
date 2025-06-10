
import os
import random
import openai
from linebot.models import TextSendMessage
from tarot_data import tarot_data

# 環境変数から OpenAI API キー取得
openai.api_key = os.getenv("OPENAI_API_KEY")

# ジャンル選択ハンドラー
def handle_genre_selection(event, line_bot_api, user_id, genre):
    if genre not in tarot_data:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ジャンルが見つかりませんでした。もう一度選択してください。")
        )
        return

    # 5枚ランダム選択
    selected_cards = random.sample(list(tarot_data[genre].keys()), 5)

    # カード結果メッセージ生成
    result_messages = []
    result_text = f"🔮【{genre}】の占い結果🔮\n\n"
    for i, card in enumerate(selected_cards, 1):
        meaning = tarot_data[genre][card]
        result_text += f"{i}枚目: {card}\n{meaning}\n\n"

    # LINEに5枚結果送信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=result_text.strip())
    )

    # 総合アドバイス作成 → GPTに投げる
    advice_prompt = f"以下は{genre}ジャンルのタロット占いの結果です。5枚のカード解釈を参考にして、ユーザーに向けた総合アドバイス（300文字以内）を日本語でわかりやすく作成してください。\n\n{result_text}"

    try:
        gpt_response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "あなたは優秀な占い師です。親しみやすく丁寧な口調で総合アドバイスを出してください。"},
                {"role": "user", "content": advice_prompt}
            ],
            max_tokens=300
        )

        summary_text = gpt_response.choices[0]["message"]["content"].strip()

        # 総合アドバイスをLINEに送信
        line_bot_api.push_message(
            user_id,
            TextSendMessage(text=f"📝【総合アドバイス】\n{summary_text}")
        )

    except Exception as e:
        # エラー時 → エラーメッセージ送信
        line_bot_api.push_message(
            user_id,
            TextSendMessage(text=f"総合アドバイスの生成時にエラーが発生しました: {str(e)}")
        )
