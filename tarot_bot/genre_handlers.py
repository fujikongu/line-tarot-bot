
import random
import openai
import os
from linebot.models import TextSendMessage, QuickReply, QuickReplyButton, MessageAction

# OpenAI API KEY 環境変数から取得
openai.api_key = os.getenv("OPENAI_API_KEY")

# ジャンルごとのタロットカード意味辞書
TAROT_TEMPLATES = {
    "恋愛運": {
        "過去": "あなたの恋愛には過去に忘れられない思い出が影響しています。",
        "現在": "今は新しい出会いやチャンスが訪れやすい時期です。",
        "未来": "未来には心から愛せる相手との進展が期待できます。",
        "対策・アドバイス": "自分の感情に素直になりましょう。新しい関係を恐れずに進んで。",
        "最終結果": "あなたの魅力が高まり、望んだ恋愛関係が築けそうです。"
    },
    "仕事運": {
        "過去": "過去の努力が現在の基盤となっています。",
        "現在": "現在はチャンスが巡ってきています。積極的に行動を。",
        "未来": "昇進や新たなプロジェクトへの参加が期待できます。",
        "対策・アドバイス": "柔軟な思考とチームワークが成功の鍵になります。",
        "最終結果": "仕事で大きな成果を上げ、評価が高まるでしょう。"
    },
    "金運": {
        "過去": "過去の出費や投資が現在の状況に影響しています。",
        "現在": "今は計画的なお金の使い方が重要な時期です。",
        "未来": "収入が増えるチャンスがありますが、慎重な管理が必要です。",
        "対策・アドバイス": "貯蓄と投資のバランスを見直しましょう。",
        "最終結果": "安定した金運を築くことができるでしょう。"
    },
    "結婚": {
        "過去": "過去の恋愛経験が結婚観に影響を与えています。",
        "現在": "パートナーとの関係が深まる時期です。",
        "未来": "結婚に向けた具体的な動きがありそうです。",
        "対策・アドバイス": "率直なコミュニケーションを心がけましょう。",
        "最終結果": "お互いに信頼し合える良い結婚生活が築けます。"
    },
    "今日の運勢": {
        "過去": "最近の出来事が今日の気分に影響を与えています。",
        "現在": "新しいアイデアやチャンスが舞い込みやすい日です。",
        "未来": "思いがけない嬉しいニュースがあるかもしれません。",
        "対策・アドバイス": "柔軟な姿勢で一日を楽しみましょう。",
        "最終結果": "充実感と達成感を味わえる一日になるでしょう。"
    }
}

def send_genre_selection(event, line_bot_api):
    quick_reply_buttons = [
        QuickReplyButton(action=MessageAction(label=genre, text=genre))
        for genre in TAROT_TEMPLATES.keys()
    ]

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text="✅パスワード認証成功！ジャンルを選んでください。",
            quick_reply=QuickReply(items=quick_reply_buttons)
        )
    )

def send_tarot_reading(event, genre, line_bot_api):
    if genre not in TAROT_TEMPLATES:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ 選択されたジャンルが存在しません。")
        )
        return

    cards = list(TAROT_TEMPLATES[genre].items())

    reading_text = "🔮【{}のタロット占い】🔮\n\n".format(genre)
    for i, (position, meaning) in enumerate(cards, 1):
        reading_text += "■ {}枚目 [{}] → {}\n".format(i, position, meaning)

    # ChatGPT API 呼び出し用プロンプト作成
    prompt_text = "あなたはプロのタロット占い師です。\n"
    prompt_text += f"ジャンル：{genre} の占い結果は以下のとおりです。\n\n"
    for i, (position, meaning) in enumerate(cards, 1):
        prompt_text += f"{i}枚目 [{position}] → {meaning}\n"
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
