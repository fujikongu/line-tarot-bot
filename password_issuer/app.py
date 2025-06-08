
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

# HTML template
HTML_TEMPLATE = '''
<!doctype html>
<html lang="ja">
  <head>
    <meta charset="utf-8">
    <title>パスワード発行</title>
    <style>
      body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
      button {{ padding: 15px 30px; font-size: 18px; cursor: pointer; }}
    </style>
  </head>
  <body>
    <h1>パスワード発行</h1>
    <form method="post">
      <button type="submit">発行する</button>
    </form>
    {% if password %}
      <h2>発行されたパスワード: {{ password }}</h2>
    {% endif %}
  </body>
</html>
'''

def get_passwords():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = { "Authorization": f"token {GITHUB_TOKEN}" }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    content = base64.b64decode(response.json()["content"]).decode("utf-8")
    return json.loads(content), response.json()["sha"]

def update_passwords(passwords, sha):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = { "Authorization": f"token {GITHUB_TOKEN}" }
    updated_content = base64.b64encode(json.dumps(passwords, indent=2, ensure_ascii=False).encode("utf-8")).decode("utf-8")
    data = {
        "message": "Update passwords.json",
        "content": updated_content,
        "sha": sha
    }
    response = requests.put(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()

@app.route("/", methods=["GET", "POST"])
def issue_password():
    password = None
    if request.method == "POST":
        passwords, sha = get_passwords()
        unused_passwords = [p for p in passwords if not p.get("used")]
        if unused_passwords:
            selected = random.choice(unused_passwords)
            selected["used"] = True
            password = selected["password"]
            update_passwords(passwords, sha)
        else:
            password = "在庫切れ"
    return render_template_string(HTML_TEMPLATE, password=password)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
