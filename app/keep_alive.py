from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run():
    # Use port 8080 or whatever Render assigns
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()