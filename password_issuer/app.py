from flask import Flask, render_template_string, jsonify
import json
import secrets
import os

app = Flask(__name__)

# パスワードを保存するファイル
PASSWORD_FILE = 'passwords.json'

# HTMLテンプレート
HTML_TEMPLATE = """
<!doctype html>
<html>
  <head>
    <title>パスワード発行フォーム</title>
  </head>
  <body>
    <h1>あなたのパスワード</h1>
    <p style="font-size: 24px; font-weight: bold;">{{ password }}</p>
    <p>このパスワードをLINEに入力して占いを開始してください。</p>
  </body>
</html>
"""

def load_passwords():
    if os.path.exists(PASSWORD_FILE):
        with open(PASSWORD_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return []

def save_password(password):
    passwords = load_passwords()
    passwords.append(password)
    with open(PASSWORD_FILE, 'w', encoding='utf-8') as f:
        json.dump(passwords, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    # ランダムなパスワードを生成（例: mem1234）
    password = f"mem{secrets.randbelow(9000) + 1000}"
    save_password(password)
    return render_template_string(HTML_TEMPLATE, password=password)

# Render対応（0.0.0.0バインディング）
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
