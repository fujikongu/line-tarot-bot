
import os
import json
import random
from flask import Flask, jsonify

app = Flask(__name__)

PASSWORDS_JSON_PATH = "passwords.json"

def load_passwords():
    with open(PASSWORDS_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_passwords(passwords):
    with open(PASSWORDS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(passwords, f, ensure_ascii=False)

@app.route("/", methods=["GET"])
def index():
    return "Password Issuer is running."

@app.route("/issue-password", methods=["GET"])
def issue_password():
    new_pass = f"mem{random.randint(1000, 9999)}"
    passwords = load_passwords()
    passwords.append(new_pass)
    save_passwords(passwords)
    html = f"""
    <html>
        <head><meta charset='utf-8'><title>あなたのパスワード</title></head>
        <body style='font-size: 2em; text-align: center; padding-top: 50px;'>
            <div>あなたのパスワード</div>
            <div style='font-weight: bold; color: #333;'>{new_pass}</div>
            <p style='font-size: 0.8em;'>このパスワードをLINEに入力して占いを開始してください。</p>
        </body>
    </html>
    """
    return html

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
