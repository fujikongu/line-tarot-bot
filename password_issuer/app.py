from flask import Flask, request, jsonify
import json
import random
import string
import os

app = Flask(__name__)
PASSWORD_FILE = "passwords.json"

def load_passwords():
    if os.path.exists(PASSWORD_FILE):
        with open(PASSWORD_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_passwords(passwords):
    with open(PASSWORD_FILE, "w", encoding="utf-8") as f:
        json.dump(passwords, f, indent=2, ensure_ascii=False)

def generate_password():
    return "mem" + ''.join(random.choices(string.digits, k=4))

@app.route("/generate", methods=["POST"])
def generate():
    passwords = load_passwords()
    new_password = generate_password()
    passwords.append({"password": new_password})
    save_passwords(passwords)
    return jsonify({"password": new_password})

@app.route("/")
def index():
    return "パスワード発行サービスへようこそ"

if __name__ == "__main__":
    app.run(debug=True)
