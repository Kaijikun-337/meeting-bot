# app/keep_alive.py
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running!", 200

def keep_alive():
    app.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':
    keep_alive()