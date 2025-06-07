
import os
import json
import requests
import base64
import random
from flask import Flask

app = Flask(__name__)

# GitHub トークンと URL
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO_URL = "https://github.com/fujikongu/line-tarot-bot"
PASSWORDS_JSON_URL = GITHUB_REPO_URL.replace("github.com", "api.github.com/repos") + "/contents/password_issuer/passwords.json"

# GitHub から passwords.json を取得
def get_passwords():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(PASSWORDS_JSON_URL, headers=headers)
    r.raise_for_status()
    content = r.json()["content"]
    decoded_content = base64.b64decode(content).decode("utf-8")
    return json.loads(decoded_content), r.json()["sha"]

# GitHub に passwords.json を更新
def update_passwords(passwords, sha):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    updated_content = base64.b64encode(json.dumps(passwords, ensure_ascii=False, indent=2).encode("utf-8")).decode("utf-8")
    data = {
        "message": "Add new password",
        "content": updated_content,
        "sha": sha
    }
    r = requests.put(PASSWORDS_JSON_URL, headers=headers, data=json.dumps(data))
    r.raise_for_status()

# ランダムパスワード生成
def generate_password():
    return f"mem{random.randint(1000, 9999)}"

@app.route("/issue-password", methods=["GET"])
def issue_password():
    try:
        passwords, sha = get_passwords()
        new_password = generate_password()

        # 重複防止
        existing_passwords = [entry["password"] for entry in passwords]
        while new_password in existing_passwords:
            new_password = generate_password()

        # 追加
        passwords.append({"password": new_password, "used": False})
        update_passwords(passwords, sha)

        return f"発行パスワード: {new_password}"

    except Exception as e:
        print(f"[ERROR] {e}")
        return f"エラーが発生しました: {e}"

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
