
import os
import json
import base64
import requests
import random
from flask import Flask, request, abort, render_template_string
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

REPO_NAME = "fujikongu/line-tarot-bot"
FILE_PATH = "password_issuer/passwords.json"
GITHUB_API_URL = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>パスワード発行</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            margin-top: 100px;
        }
        h1 {
            font-size: 48px;
        }
        button {
            font-size: 36px;
            padding: 20px 40px;
            background-color: #007BFF;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
        }
        button:hover {
            background-color: #0056b3;
        }
        .password {
            margin-top: 20px;
            font-size: 36px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <h1>パスワード発行</h1>
    <form method="POST" action="/issue-password">
        <button type="submit">発行する</button>
    </form>
    {% if password %}
        <div class="password">発行されたパスワード: {{ password }}</div>
    {% endif %}
</body>
</html>
'''

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/issue-password", methods=["POST"])
def issue_password():
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }

    response = requests.get(GITHUB_API_URL, headers=headers)
    if response.status_code != 200:
        return f"Failed to fetch passwords.json: {response.text}", 500

    content = response.json()
    sha = content["sha"]
    passwords = json.loads(base64.b64decode(content["content"]).decode("utf-8"))

    unused_passwords = [p for p in passwords if not p["used"]]
    if not unused_passwords:
        return "No available passwords.", 500

    selected_password = random.choice(unused_passwords)
    selected_password["used"] = True

    updated_content = base64.b64encode(json.dumps(passwords, indent=4).encode("utf-8")).decode("utf-8")
    update_data = {
        "message": "Update passwords.json",
        "content": updated_content,
        "sha": sha,
    }

    update_response = requests.put(GITHUB_API_URL, headers=headers, data=json.dumps(update_data))
    if update_response.status_code not in [200, 201]:
        return f"Failed to update passwords.json: {update_response.text}", 500

    return render_template_string(HTML_TEMPLATE, password=selected_password["password"])

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="占いBotへようこそ！")
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
