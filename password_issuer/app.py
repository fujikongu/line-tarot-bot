
import os
import json
import requests
import base64
import random
from flask import Flask, request, render_template_string

app = Flask(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = "fujikongu/line-tarot-bot"
FILE_PATH = "password_issuer/passwords.json"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>パスワード発行</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding-top: 50px; }
        button { font-size: 20px; padding: 15px 30px; background-color: #007bff; color: white; border: none; border-radius: 8px; cursor: pointer; }
        button:hover { background-color: #0056b3; }
        .password { margin-top: 20px; font-size: 24px; color: #333; }
    </style>
</head>
<body>
    <h1>パスワード発行</h1>
    <form method="post">
        <button type="submit">発行する</button>
    </form>
    {% if password %}
    <div class="password">発行されたパスワード: {{ password }}</div>
    {% endif %}
</body>
</html>
"""

def get_passwords():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}" }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    content = response.json()
    file_content = base64.b64decode(content["content"]).decode("utf-8")
    return json.loads(file_content), content["sha"]

def update_passwords(passwords, sha):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    updated_content = base64.b64encode(json.dumps(passwords, indent=4, ensure_ascii=False).encode()).decode()
    data = {
        "message": "Update passwords.json",
        "content": updated_content,
        "sha": sha
    }
    response = requests.put(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()

@app.route("/issue-password", methods=["GET", "POST"])
def issue_password():
    password = None
    if request.method == "POST":
        passwords, sha = get_passwords()
        unused_passwords = [p for p in passwords if not p["used"]]
        if unused_passwords:
            selected_password = random.choice(unused_passwords)
            selected_password["used"] = True
            update_passwords(passwords, sha)
            password = selected_password["password"]
    return render_template_string(HTML_TEMPLATE, password=password)

@app.route("/")
def home():
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
