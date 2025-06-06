
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import json
import os
import github
import random

app = Flask(__name__)

# 環境変数からLINEアクセストークンとシークレットを取得
line_bot_api = LineBotApi(os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET"))

# トップページ確認用
@app.route('/')
def index():
    return 'Your service is running!'

# パスワード発行用
@app.route('/issue-password')
def issue_password():
    # GitHubリポジトリの情報
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
    REPO_NAME = "fujikongu/line-tarot-bot"
    FILE_PATH = "password_issuer/passwords.json"

    # ランダムなパスワード生成
    new_password = f"mem{random.randint(10000, 99999)}"

    # GitHubに接続
    g = github.Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    contents = repo.get_contents(FILE_PATH)
    passwords = json.loads(contents.decoded_content.decode())

    # 新しいパスワードをリストに追加
    passwords.append(new_password)

    # 更新内容をコミット
    repo.update_file(contents.path, "Update passwords.json", json.dumps(passwords, indent=4), contents.sha)

    return f"New password issued: {new_password}"

# LINEのコールバック処理
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# メッセージイベントの処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    # GitHub上の passwords.json を読み込む
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
    REPO_NAME = "fujikongu/line-tarot-bot"
    FILE_PATH = "password_issuer/passwords.json"

    g = github.Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    contents = repo.get_contents(FILE_PATH)
    valid_passwords = json.loads(contents.decoded_content.decode())

    if user_message in valid_passwords:
        # 認証成功 → パスワードを削除
        valid_passwords.remove(user_message)
        repo.update_file(contents.path, "Remove used password", json.dumps(valid_passwords, indent=4), contents.sha)

        # ここは仮の成功メッセージ
        reply_text = "✅ パスワード認証成功！これから占いを始めます。"
    else:
        reply_text = "パスワードを入力してください。\n例：mem1091"

    # LINEに返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

# アプリ起動
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
