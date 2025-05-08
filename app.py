from flask import Flask, request
import requests
import psycopg2
import os

app = Flask(__name__)

# Token xác minh và Page Access Token của bạn
VERIFY_TOKEN = "mytoken123"
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")  # Đặt trong Render Environment

# Kết nối PostgreSQL (dùng DATABASE_URL từ biến môi trường)
DATABASE_URL = os.environ.get("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Tạo bảng nếu chưa có
cursor.execute("""
    CREATE TABLE IF NOT EXISTS links (
        name TEXT PRIMARY KEY,
        url TEXT
    );
""")
conn.commit()

def save_link_to_db(name, url):
    cursor.execute("""
        INSERT INTO links (name, url)
        VALUES (%s, %s)
        ON CONFLICT (name) DO UPDATE SET url = EXCLUDED.url;
    """, (name, url))
    conn.commit()

def get_link(name):
    cursor.execute("SELECT url FROM links WHERE name=%s;", (name,))
    result = cursor.fetchone()
    return result[0] if result else None

def delete_link(name):
    cursor.execute("DELETE FROM links WHERE name=%s;", (name,))
    conn.commit()

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
                    try:
                        save_name, save_url = text[6:].split(' ', 1)
                        save_link_to_db(save_name, save_url)
                        send_message(sender, f"Đã lưu {save_name} với link: {save_url}")
                    except ValueError:
                        send_message(sender, "Sai cú pháp! Dùng: /save <tên> <link>")

                elif text.startswith('/get '):
                    search_name = text[5:]
                    link = get_link(search_name)
                    if link:
                        send_message(sender, f"Link của {search_name} là: {link}")
                    else:
                        send_message(sender, f"Không tìm thấy link cho {search_name}")

                elif text.startswith('/del '):
                    delete_name = text[5:]
                    if get_link(delete_name):
                        delete_link(delete_name)
                        send_message(sender, f"Đã xóa link của {delete_name}")
                    else:
                        send_message(sender, f"Không tìm thấy link để xóa cho {delete_name}")
    return "ok", 200

def send_message(psid, message):
    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": psid},
        "message": {"text": message}
    }
    requests.post(url, json=payload)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
