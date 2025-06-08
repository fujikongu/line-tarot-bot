
import os
import json
import random
import string
import base64
import requests
from flask import Flask, request, render_template_string, redirect, url_for

app = Flask(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = "fujikongu"
REPO_NAME = "line-tarot-bot"
FILE_PATH = "password_issuer/passwords.json"
GITHUB_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"

def get_passwords():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(GITHUB_API_URL, headers=headers)
    if response.status_code == 200:
        content = response.json()
        file_content = base64.b64decode(content["content"]).decode("utf-8-sig")
        sha = content["sha"]
        passwords = json.loads(file_content)
        return passwords, sha
    else:
        raise Exception(f"Failed to fetch passwords.json: {response.status_code}, {response.text}")

def update_passwords(passwords, sha):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    updated_content = json.dumps(passwords, ensure_ascii=False, indent=4)
    encoded_content = base64.b64encode(updated_content.encode("utf-8-sig")).decode("utf-8")
    data = {
        "message": "Update passwords.json",
        "content": encoded_content,
        "sha": sha
    }
    response = requests.put(GITHUB_API_URL, headers=headers, data=json.dumps(data))
    if response.status_code == 200 or response.status_code == 201:
        return True
    else:
        raise Exception(f"Failed to update passwords.json: {response.status_code}, {response.text}")

def generate_random_password():
    prefix = "mem"
    suffix = "".join(random.choices(string.digits, k=4))
    return prefix + suffix

@app.route("/issue-password", methods=["GET", "POST"])
def issue_password():
    if request.method == "POST":
        try:
            passwords, sha = get_passwords()
            while True:
                new_password = generate_random_password()
                if all(p["password"] != new_password for p in passwords):
                    break
            passwords.append({"password": new_password, "used": False})
            update_passwords(passwords, sha)
            return render_template_string("""
                <h1>OK - Password Issued Successfully</h1>
                <p style='font-size:24px;'>{{ new_password }}</p>
                <a href="{{ url_for('issue_password') }}">Back</a>
            """, new_password=new_password)
        except Exception as e:
            return f"Error occurred: {str(e)}"
    return render_template_string("""
        <h1>Issue Password</h1>
        <form method="post">
            <button type="submit">Issue Password</button>
        </form>
    """)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
