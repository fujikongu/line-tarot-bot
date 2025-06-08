
import os
import json
import requests
import base64
from flask import Flask, request, render_template_string

app = Flask(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PASSWORDS_URL = "https://api.github.com/repos/fujikongu/line-tarot-bot/contents/password_issuer/passwords.json"

# パスワード取得
def get_passwords():
    try:
        print(">>> STEP1: get_passwords called")
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        response = requests.get(PASSWORDS_URL, headers=headers)
        print(f">>> STEP1-1: response.status_code = {response.status_code}")
        if response.status_code == 200:
            content = response.json()["content"]
            passwords = json.loads(base64.b64decode(content).decode("utf-8"))
            print(">>> STEP1-2: passwords loaded")
            return passwords
        else:
            print(">>> STEP1-3: failed to get passwords.json")
            return []
    except Exception as e:
        print(">>> ERROR in get_passwords:", e)
        return []

# パスワード更新
def update_passwords(passwords):
    try:
        print(">>> STEP2: update_passwords called")
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        get_response = requests.get(PASSWORDS_URL, headers=headers)
        sha = get_response.json()["sha"]
        print(">>> STEP2-1: sha fetched")

        updated_content = base64.b64encode(json.dumps(passwords, ensure_ascii=False, indent=4).encode("utf-8")).decode("utf-8")
        data = {
            "message": "Update passwords.json",
            "content": updated_content,
            "sha": sha
        }
        put_response = requests.put(PASSWORDS_URL, headers=headers, data=json.dumps(data))
        print(f">>> STEP2-2: put_response.status_code = {put_response.status_code}")
        if put_response.status_code == 200:
            print(">>> STEP2-3: passwords updated successfully")
        else:
            print(">>> STEP2-4: failed to update passwords.json", put_response.text)
    except Exception as e:
        print(">>> ERROR in update_passwords:", e)

# パスワード生成
def generate_password():
    import random
    return "mem" + str(random.randint(1000, 9999))

@app.route("/issue-password", methods=["GET", "POST"])
def issue_password():
    try:
        print(">>> STEP3: issue_password called")
        if request.method == "POST":
            print(">>> STEP3-1: POST request detected")
            passwords = get_passwords()
            print(">>> STEP3-2: passwords fetched:", passwords)

            new_password = generate_password()
            print(">>> STEP3-3: new_password =", new_password)

            passwords.append({"password": new_password, "used": False})
            update_passwords(passwords)
            print(">>> STEP3-4: passwords updated")

            return render_template_string("""
                <h2>新しいパスワード: {{password}}</h2>
                <form method='post'><button type='submit'>発行する</button></form>
            """, password=new_password)
        
        print(">>> STEP3-5: GET request detected")
        return render_template_string("""
            <h2>パスワード発行</h2>
            <form method='post'><button type='submit'>発行する</button></form>
        """)
    except Exception as e:
        print(">>> ERROR in issue_password:", e)
        return "Internal Server Error", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
