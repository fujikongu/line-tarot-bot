
import random
import openai
import os
from linebot.models import TextSendMessage
from .genre_file_map import genre_file_map

# ChatGPT API Key セット
openai.api_key = os.getenv("OPENAI_API_KEY")

def send_tarot_reading(event, genre, line_bot_api):
    tarot_template = genre_file_map.get(genre)
    if not tarot_template:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ジャンルデータが見つかりませんでした。")
        )
        return

    # 5枚ランダム選択
    cards = random.sample(tarot_template["cards"], 5)

    # 各カードの説明文ブロック作成
    card_text_blocks = ""
    for i, card in enumerate(cards, 1):
        card_text_blocks += f"{i}枚目は『{card['name']}』のカードです。{card['meaning']}。\n\n"

    # ChatGPT API 用プロンプト作成
    prompt = f"""
あなたは優秀な占い師です。
以下のタロットカード5枚の結果をもとに、ジャンル「{genre}」について全体の占い結果を1500文字程度の自然な文章としてまとめてください。
・最初に全体の占い傾向（リード文）を1〜2文書く
・次に各カードの意味を自然な段落として説明する（箇条書きNG、文章としてつなげる）
・最後に総合アドバイス段落（400文字以上）を必ず入れる
・全体で1200〜1500文字程度になるように調整する

【カード結果】  
{card_text_blocks}
"""

    # ChatGPT API 呼び出し
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=2000
        )

        advice_text = response['choices'][0]['message']['content']

        # 最終メッセージ整形
        final_result_text = f"🔮【{genre}の占い結果】🔮\n\n{advice_text}"

        # LINE 返信
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=final_result_text)
        )

    except Exception as e:
        # エラー時はエラーメッセージを返す
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"❌占い文章の生成中にエラーが発生しました。\n{str(e)}")
        )
