
import random
import openai
import os
from linebot.models import TextSendMessage, QuickReply, QuickReplyButton, MessageAction

from tarot_data import TAROT_CARDS, TAROT_MEANINGS

# OpenAI API KEY 環境変数から取得
openai.api_key = os.getenv("OPENAI_API_KEY")

def send_genre_selection(event, line_bot_api):
    quick_reply_buttons = [
        QuickReplyButton(action=MessageAction(label=genre, text=genre))
        for genre in TAROT_MEANINGS.keys()
    ]

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text="✅パスワード認証成功！ジャンルを選んでください。",
            quick_reply=QuickReply(items=quick_reply_buttons)
        )
    )

def send_tarot_reading(event, genre, line_bot_api):
    if genre not in TAROT_MEANINGS:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ 選択されたジャンルが存在しません。")
        )
        return

    # 5枚ランダム抽出
    selected_cards = random.sample(TAROT_CARDS, 5)
    reading_text = "🔮【{}のタロット占い】🔮\n\n".format(genre)

    card_results = []  # AIプロンプト用

    for i, card in enumerate(selected_cards, 1):
        # 正逆ランダム
        orientation = random.choice(["正位置", "逆位置"])
        meaning = TAROT_MEANINGS[genre][card][orientation]
        reading_text += "■ {}枚目 [{} / {}] → {}\n".format(i, card, orientation, meaning)

        card_results.append(f"{i}枚目 [{card}] / {orientation} → {meaning}")

    # ChatGPT API 用プロンプト作成
    prompt_text = "あなたはプロのタロット占い師です。\n"
    prompt_text += f"ジャンル：{genre} の占い結果は以下のとおりです。\n\n"
    for result in card_results:
        prompt_text += result + "\n"
    prompt_text += "\nこの結果をもとに1500文字程度のプロのタロット占い総合アドバイスを書いてください。\n"
    prompt_text += "必ず自然な日本語で丁寧に整えて、読みやすい形にしてください。\n"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "あなたはプロのタロット占い師です。"},
                {"role": "user", "content": prompt_text}
            ],
            max_tokens=2000,
            temperature=0.7
        )

        ai_advice = response["choices"][0]["message"]["content"].strip()

    except Exception as e:
        ai_advice = f"❌ ChatGPT API呼び出しエラーが発生しました：{e}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reading_text + "\n\n✨総合アドバイス✨\n" + ai_advice)
    )
