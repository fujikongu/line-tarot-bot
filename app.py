
import os
import json
import requests
import base64
import random
import string
from flask import Flask, request, render_template_string

app = Flask(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = "fujikongu/line-tarot-bot"
FILE_PATH = "password_issuer/passwords.json"

HTML_TEMPLATE = """
<html>
    <head>
        <meta charset="utf-8">
        <title>パスワード発行</title>
        <style>
            body {
                text-align: center;
                font-family: Arial, sans-serif;
                margin-top: 50px;
            }
            h1 {
                font-size: 48px;
            }
            button {
                font-size: 32px;
                padding: 20px 40px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
            }
            button:hover {
                background-color: #0056b3;
            }
        </style>
    </head>
    <body>
        <h1>パスワード発行</h1>
        <form method="post" action="/issue-password">
            <button type="submit">発行する</button>
        </form>
        {% if password %}
            <h2>発行されたパスワード: {{ password }}</h2>
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
    content = response.json()
    file_content = base64.b64decode(content["content"]).decode("utf-8")
    sha = content["sha"]
    passwords = json.loads(file_content)
    return passwords, sha

def update_passwords(passwords, sha):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    updated_content = json.dumps(passwords, ensure_ascii=False, indent=4)
    b64_content = base64.b64encode(updated_content.encode("utf-8")).decode("utf-8")
    data = {
        "message": "Update passwords.json",
        "content": b64_content,
        "sha": sha
    }
    response = requests.put(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

def generate_password(length=8):
    return "mem" + ''.join(random.choices(string.digits, k=4))

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/issue-password", methods=["POST"])
def issue_password():
    passwords, sha = get_passwords()
    new_password = generate_password()
    passwords.append({"password": new_password, "used": False})
    update_passwords(passwords, sha)
    return render_template_string(HTML_TEMPLATE, password=new_password)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
