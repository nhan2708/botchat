from flask import Flask, request
import requests

app = Flask(__name__)

VERIFY_TOKEN = "mytoken123"
PAGE_ACCESS_TOKEN = "EAAffNumwM40BO9fetZCNa7FjvE7OnhY6Yxex2EYJRXiqRNDdbQiuyv2E9AsTjzepZCX21C1oyC0m436ZB5yFNZA9UffZCoqEWOnCQnODcWnr5W5ympocEsZBCqnqlZARdanZBl4Twnyp3dLZBnKCApVC0VS2IR7Bi9hMujnMIKmQMucOae4jikWutAKLJXGHFNAZBYlQZDZD"

@app.route("/webhook", methods=['GET'])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Verification failed", 403

@app.route("/webhook", methods=['POST'])
def webhook():
    data = request.get_json()
    for entry in data['entry']:
        for msg in entry['messaging']:
            if 'message' in msg:
                sender = msg['sender']['id']
                text = msg['message'].get('text', '')
                if text.startswith('/save '):
                    save_name, save_link = text[6:].split(' ', 1)
                    # Lưu tên và link vào DB ở đây
                    send_message(sender, f"Đã lưu {save_name} với link: {save_link}")
    return "ok", 200

def send_message(psid, message):
    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": psid},
        "message": {"text": message}
    }
    requests.post(url, json=payload)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

