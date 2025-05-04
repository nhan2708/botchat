from flask import Flask, request
import requests

app = Flask(__name__)

VERIFY_TOKEN = "mytoken123"
PAGE_ACCESS_TOKEN = "YOUR_PAGE_ACCESS_TOKEN"

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
    app.run(port=5000)
