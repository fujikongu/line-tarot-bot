
from flask import Flask, render_template_string
import requests
import json
import random
import string
import os

app = Flask(__name__)

# GitHub API設定
url = "https://api.github.com/repos/fujikongu/line-tarot-bot/contents/password_issuer/passwords.json"
token = os.getenv("GITHUB_TOKEN")

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
}

# HTMLテンプレート
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>パスワード発行</title>
</head>
<body>
    {% if password %}
        <h2>あなたのパスワード</h2>
        <p><strong>{{ password }}</strong></p>
        <p>このパスワードをLINEに入力して占いを開始してください。</p>
    {% else %}
        <p>Password Issuer is running.</p>
    {% endif %}
</body>
</html>
"""

# パスワード生成
def generate_password(length=8):
    return "mem" + ''.join(random.choices(string.digits, k=length - 3))

# GitHubからpasswords.json取得
def get_passwords_json():
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = r.json()["content"]
        encoding = r.json()["encoding"]
        if encoding == "base64":
            import base64
            decoded = base64.b64decode(content).decode("utf-8")
            return json.loads(decoded), r.json()["sha"]
        elif r.status_code == 404:
            return [], None
        else:
            raise Exception(f"Failed to fetch file: {r.text}")
    elif r.status_code == 404:
        # ファイルがない場合は新規作成扱い
        return [], None
    else:
        raise Exception(f"Failed to fetch file: {r.text}")

# GitHubにpasswords.json更新
def update_passwords_json(new_password):
    passwords, sha = get_passwords_json()
    passwords.append(new_password)
    updated_content = json.dumps(passwords, ensure_ascii=False, indent=2)

    import base64
    b64_content = base64.b64encode(updated_content.encode()).decode()

    data = {
        "message": "Update passwords.json",
        "content": b64_content,
        "branch": "main"
    }
    if sha:
        data["sha"] = sha

    r = requests.put(url, headers=headers, data=json.dumps(data))
    if r.status_code not in [200, 201]:
        raise Exception(f"Failed to update file: {r.text}")

# ルート
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, password=None)

# パスワード発行
@app.route("/issue-password")
def issue_password():
    new_pass = generate_password()
    update_passwords_json(new_pass)
    return render_template_string(HTML_TEMPLATE, password=new_pass)

# main
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
