import os
import json
import base64
import requests
from flask import Flask, request, render_template_string
from datetime import datetime
import random
import string

app = Flask(__name__)

# GitHubのリポジトリ情報
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = "fujikongu/line-tarot-bot"
FILE_PATH = "password_issuer/passwords.json"

# GitHub API URL
GITHUB_API_URL = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"

# パスワードをランダム生成
def generate_password(length=8):
    return "mem" + "".join(random.choices(string.digits, k=4))

# GitHubからpasswords.json取得
def get_passwords():
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(GITHUB_API_URL, headers=headers)
    response.raise_for_status()
    content = base64.b64decode(response.json()["content"])
    return json.loads(content), response.json()["sha"]

# GitHubへpasswords.json更新
def update_passwords(passwords, sha):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    new_content = base64.b64encode(json.dumps(passwords, indent=4, ensure_ascii=False).encode()).decode()
    data = {
        "message": f"Update passwords.json at {datetime.utcnow().isoformat()}",
        "content": new_content,
        "sha": sha
    }
    response = requests.put(GITHUB_API_URL, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

@app.route("/", methods=["GET", "POST"])
def issue_password():
    message = ""
    if request.method == "POST":
        try:
            passwords, sha = get_passwords()
            # 未使用のパスワードがあるか確認
            unused_password = None
            for entry in passwords:
                if not entry.get("used", False):
                    unused_password = entry
                    break

            if unused_password:
                # 未使用パスワードを利用
                password = unused_password["password"]
                unused_password["used"] = True
            else:
                # 新規発行
                password = generate_password()
                passwords.append({"password": password, "used": True})

            # GitHubに更新
            update_passwords(passwords, sha)
            message = f"発行されたパスワード: {password}"
        except Exception as e:
            message = f"エラーが発生しました: {str(e)}"

    html = """
    <html>
    <body style="font-family: Arial, sans-serif; text-align: center; padding-top: 50px;">
        <h1 style="font-size: 32px;">パスワード発行</h1>
        <form method="post">
            <button type="submit" style="
                font-size: 20px;
                padding: 15px 40px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
            ">発行する</button>
        </form>
        <p style="margin-top: 20px; font-size: 18px; color: green;">{{ message }}</p>
    </body>
    </html>
    """
    return render_template_string(html, message=message)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
