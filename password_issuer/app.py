
import os
import json
import random
import string
import base64
import requests
from flask import Flask, request, render_template_string

app = Flask(__name__)

# GitHub情報
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = "fujikongu/line-tarot-bot"
FILE_PATH = "password_issuer/passwords.json"

# HTMLテンプレート（日本語＋ボタン大きく）
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>パスワード発行</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding-top: 50px; }
        h1 { font-size: 36px; color: #333; }
        .button {
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 20px 40px;
            text-align: center;
            text-decoration: none;
            font-size: 24px;
            border-radius: 8px;
            cursor: pointer;
        }
        .password {
            margin-top: 30px;
            font-size: 28px;
            color: #d9534f;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <h1>パスワード発行</h1>
    <form method="post">
        <button type="submit" class="button">パスワードを発行する</button>
    </form>
    {% if password %}
        <div class="password">発行されたパスワード: {{ password }}</div>
    {% endif %}
</body>
</html>
"""

# GitHubからpasswords.json取得
def get_passwords():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = base64.b64decode(response.json()["content"])
        return json.loads(content), response.json()["sha"]
    else:
        return [], None

# GitHubへpasswords.json更新
def update_passwords(passwords, sha):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    content = base64.b64encode(json.dumps(passwords, indent=4, ensure_ascii=False).encode()).decode()
    data = {
        "message": "Update passwords.json",
        "content": content,
        "sha": sha
    }
    response = requests.put(url, headers=headers, json=data)
    return response.status_code in [200, 201]

# ランダムパス生成
def generate_password():
    return "mem" + ''.join(random.choices(string.digits, k=4))

@app.route("/", methods=["GET", "POST"])
def issue_password():
    password = None
    if request.method == "POST":
        passwords, sha = get_passwords()
        new_password = generate_password()
        passwords.append({"password": new_password, "used": False})
        success = update_passwords(passwords, sha)
        if success:
            password = new_password
    return render_template_string(HTML_TEMPLATE, password=password)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
