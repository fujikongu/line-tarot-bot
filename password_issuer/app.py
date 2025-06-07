import os
import json
import random
import string
import base64
import requests
from flask import Flask, request, render_template_string

app = Flask(__name__)

# 環境変数
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL")

# GitHub API用URLに変換
GITHUB_API_URL = GITHUB_REPO_URL.replace("https://github.com/", "https://api.github.com/repos/")
PASSWORDS_JSON_URL = GITHUB_API_URL + "/contents/password_issuer/passwords.json"

# HTMLテンプレート
HTML_TEMPLATE = """
<!doctype html>
<title>Issue Password</title>
<h1>Issue Random Password</h1>
<form method="post">
    <button type="submit">Issue Password</button>
</form>
{% if password %}
    <p>Issued Password: <strong>{{ password }}</strong></p>
{% endif %}
"""

# GitHubからpasswords.jsonを取得
def get_passwords():
    headers = {"Authorization": f"token {GITHUB_TOKEN}" }
    r = requests.get(PASSWORDS_JSON_URL, headers=headers)
    r.raise_for_status()
    content = r.json()["content"]
    decoded = base64.b64decode(content).decode("utf-8")
    return json.loads(decoded), r.json()["sha"]

# GitHubにpasswords.jsonをアップロード
def update_passwords(passwords, sha):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    updated_content = base64.b64encode(json.dumps(passwords, ensure_ascii=False, indent=4).encode("utf-8")).decode("utf-8")
    data = {
        "message": "Add new password",
        "content": updated_content,
        "sha": sha
    }
    r = requests.put(PASSWORDS_JSON_URL, headers=headers, data=json.dumps(data))
    r.raise_for_status()

# ランダムパスワード生成 (mem + 4桁数字)
def generate_password():
    return "mem" + ''.join(random.choices(string.digits, k=4))

@app.route("/issue-password", methods=["GET", "POST"])
def issue_password():
    password = None

    if request.method == "POST":
        # パスワード生成
        new_password = generate_password()

        try:
            passwords, sha = get_passwords()
        except Exception as e:
            return f"Failed to load passwords.json: {e}", 500

        # 既に存在しないか確認して追加
        if new_password not in passwords:
            passwords.append(new_password)

            try:
                update_passwords(passwords, sha)
                password = new_password
            except Exception as e:
                return f"Failed to update passwords.json: {e}", 500
        else:
            password = "(duplicate skipped, try again)"

    return render_template_string(HTML_TEMPLATE, password=password)

@app.route("/")
def index():
    return "Password Issuer is running."

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)