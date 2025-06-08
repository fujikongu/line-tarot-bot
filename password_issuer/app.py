
from flask import Flask, request, render_template_string
import os
import json
import random
import string
import base64
import requests

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
</head>
<body style="text-align:center;padding-top:50px;font-size:2em;">
    <h1>パスワード発行</h1>
    <form method="post">
        <button type="submit" style="font-size:2em;padding:20px 40px;">発行する</button>
    </form>
    {% if password %}
        <p>発行されたパスワード: <strong>{{ password }}</strong></p>
    {% endif %}
</body>
</html>
"""

def get_passwords():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    content = base64.b64decode(response.json()["content"])
    return json.loads(content), response.json()["sha"]

def update_passwords(passwords, sha):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    new_content = base64.b64encode(json.dumps(passwords, indent=4, ensure_ascii=False).encode()).decode()
    data = {
        "message": "Update passwords.json",
        "content": new_content,
        "sha": sha
    }
    response = requests.put(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()

def generate_password(length=8):
    return "mem" + "".join(random.choices(string.digits, k=length - 3))

@app.route("/", methods=["GET", "POST"])
def index():
    password = None
    if request.method == "POST":
        passwords, sha = get_passwords()
        new_password = generate_password()
        passwords.append({"password": new_password, "used": False})
        update_passwords(passwords, sha)
        password = new_password
    return render_template_string(HTML_TEMPLATE, password=password)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
