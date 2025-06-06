
import json
import random
import string
import requests
import os
from flask import Flask, request

app = Flask(__name__)

# 環境変数から読み込み
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_OWNER = 'fujikongu'
REPO_NAME = 'line-tarot-bot'
FILE_PATH = 'password_issuer/passwords.json'

def get_passwords_json():
    url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = r.json()
        file_content = content['content']
        encoding = content['encoding']
        if encoding == 'base64':
            import base64
            decoded_content = base64.b64decode(file_content).decode('utf-8')
            return json.loads(decoded_content), content['sha']
    raise Exception(f'Failed to fetch file: {r.text}')

def update_passwords_json(new_pass):
    passwords, sha = get_passwords_json()
    passwords.append(new_pass)

    updated_content = json.dumps(passwords, indent=4)
    import base64
    encoded_content = base64.b64encode(updated_content.encode('utf-8')).decode('utf-8')

    url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    data = {
        'message': 'Update passwords.json',
        'content': encoded_content,
        'sha': sha
    }
    r = requests.put(url, headers=headers, json=data)
    if r.status_code not in [200, 201]:
        raise Exception(f'Failed to update file: {r.text}')

def generate_password():
    prefix = 'mem'
    suffix = ''.join(random.choices(string.digits, k=4))
    return prefix + suffix

# --- ルート定義 ---
@app.route('/')
def home():
    return "Password Issuer is running."

@app.route('/issue-password', methods=['GET'])
def issue_password_page():
    return '''
        <h1>パスワード発行</h1>
        <form method="post" action="/issue-password">
            <button type="submit">発行する</button>
        </form>
    '''

@app.route('/issue-password', methods=['POST'])
def issue_password():
    new_pass = generate_password()
    update_passwords_json(new_pass)
    return f'''
        <h1>あなたのパスワード</h1>
        <p><b>{new_pass}</b></p>
        <p>このパスワードをLINEに入力して占いを開始してください。</p>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
