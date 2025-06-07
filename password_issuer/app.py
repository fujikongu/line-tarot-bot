
import os
import json
import requests
import base64
import random
import string
from flask import Flask, request, render_template_string

app = Flask(__name__)

# 環境変数から GitHub Token と Repo URL を取得
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL")

# GitHub API 用 URL を組み立て
GITHUB_API_URL = GITHUB_REPO_URL.replace("https://github.com/", "https://api.github.com/repos/")
PASSWORDS_JSON_URL = GITHUB_API_URL + "/contents/password_issuer/passwords.json"

# HTML フォームテンプレート
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Issue Password</title>
</head>
<body>
    <h1>Issue Password</h1>
    <form method="POST">
        <label for="password">Password:</label>
        <input type="text" id="password" name="password" required>
        <button type="submit">Issue</button>
    </form>
    {% if message %}
    <p>{{ message }}</p>
    {% endif %}
</body>
</html>
"""

def get_passwords_file():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(PASSWORDS_JSON_URL, headers=headers)
    response.raise_for_status()
    content = response.json()
    file_sha = content["sha"]
    file_content = json.loads(requests.get(content["download_url"]).text)
    return file_content, file_sha

def update_passwords_file(passwords, sha):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    message = "Update passwords.json"
    updated_content = json.dumps(passwords, indent=4)
    b64_content = base64.b64encode(updated_content.encode("utf-8")).decode("utf-8")

    response = requests.put(
        PASSWORDS_JSON_URL,
        headers=headers,
        json={
            "message": message,
            "content": b64_content,
            "sha": sha
        }
    )
    response.raise_for_status()

# 手入力フォーム
@app.route("/issue-password", methods=["GET", "POST"])
def issue_password():
    message = None
    if request.method == "POST":
        new_password = request.form["password"]
        try:
            passwords, sha = get_passwords_file()
            if new_password not in passwords:
                passwords.append(new_password)
                update_passwords_file(passwords, sha)
                message = f"Password '{new_password}' issued successfully."
            else:
                message = f"Password '{new_password}' already exists."
        except Exception as e:
            message = f"Error: {str(e)}"

    return render_template_string(HTML_TEMPLATE, message=message)

# ランダムパスワード自動発行
@app.route('/issue-password-auto', methods=['GET'])
def issue_password_auto():
    new_password = 'mem' + ''.join(random.choices(string.digits, k=4))
    try:
        passwords, sha = get_passwords_file()
        if new_password not in passwords:
            passwords.append(new_password)
            update_passwords_file(passwords, sha)
            return f'発行されたパス: {new_password}'
        else:
            return f'発行失敗: 既に存在するパス "{new_password}"'
    except Exception as e:
        return f'Error: {str(e)}'

# デフォルトルート
@app.route("/")
def index():
    return "Password Issuer App with Auto Issue is running."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
