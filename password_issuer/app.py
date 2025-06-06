
from flask import Flask, render_template_string, redirect
import random
import string
import json
import requests
import os
import base64

app = Flask(__name__)

# GitHubの設定
GITHUB_REPO = "fujikongu/line-tarot-bot"
GITHUB_FILE_PATH = "passwords.json"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# パスワード生成関数
def generate_password():
    return "mem" + ''.join(random.choices(string.digits, k=4))

# GitHub API経由でpasswords.jsonを更新する関数
def update_passwords_json(new_password):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 現在のファイル内容とSHA取得
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        raise Exception(f"Failed to fetch file: {r.text}")

    content = json.loads(r.text)
    sha = content["sha"]
    existing_data = json.loads(base64.b64decode(content["content"]).decode())

    # 新パス追加
    existing_data.append(new_password)

    updated_content = base64.b64encode(json.dumps(existing_data).encode()).decode()

    # GitHubへPUTで反映
    payload = {
        "message": f"Add new password {new_password}",
        "content": updated_content,
        "sha": sha
    }
    put = requests.put(url, headers=headers, json=payload)
    if put.status_code not in [200, 201]:
        raise Exception(f"Failed to update: {put.text}")

# HTMLテンプレート
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>占いパスワード発行</title>
</head>
<body>
    <h2>あなたのパスワード</h2>
    <p style="font-size: 24px;"><strong>{{ password }}</strong></p>
    <p>このパスワードをLINEに入力して占いを開始してください。</p>
</body>
</html>
"""

@app.route("/")
def issue_password():
    new_pass = generate_password()
    update_passwords_json(new_pass)
    return render_template_string(HTML_TEMPLATE, password=new_pass)

if __name__ == "__main__":
    app.run(debug=True)
