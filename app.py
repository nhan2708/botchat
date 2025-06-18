from flask import Flask, request
import psycopg2
import os
import requests
import urllib.parse as up

app = Flask(__name__)

# Facebook tokens
VERIFY_TOKEN = "mytoken123"
PAGE_ACCESS_TOKEN = os.getenv("EAAffNumwM40BO9fetZCNa7FjvE7OnhY6Yxex2EYJRXiqRNDdbQiuyv2E9AsTjzepZCX21C1oyC0m436ZB5yFNZA9UffZCoqEWOnCQnODcWnr5W5ympocEsZBCqnqlZARdanZBl4Twnyp3dLZBnKCApVC0VS2IR7Bi9hMujnMIKmQMucOae4jikWutAKLJXGHFNAZBYlQZDZD")

# Parse PostgreSQL URL
DATABASE_URL = os.environ.get("DATABASE_URL")

# Parse the database URL correctly
up.uses_netloc.append("postgres")
url = up.urlparse(DATABASE_URL)

conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port,
    sslmode='require'
)
cursor = conn.cursor()

# Create table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS links (
        name TEXT PRIMARY KEY,
        url TEXT
    )
""")
conn.commit()

# DB helpers
def save_link_to_db(name, url):
    cursor.execute("""
        INSERT INTO links (name, url)
        VALUES (%s, %s)
        ON CONFLICT (name) DO UPDATE SET url = EXCLUDED.url
    """, (name, url))
    conn.commit()

def get_link(name):
    cursor.execute("SELECT url FROM links WHERE name=%s", (name,))
    result = cursor.fetchone()
    return result[0] if result else None

def delete_link(name):
    cursor.execute("DELETE FROM links WHERE name=%s", (name,))
    conn.commit()

# Facebook Webhook
@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Verification failed", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    for entry in data.get("entry", []):
        for msg in entry.get("messaging", []):
            if 'message' in msg:
                sender = msg['sender']['id']
                text = msg['message'].get('text', '')

                if text.startswith('/save '):
                    try:
                        save_name, save_url = text[6:].split(' ', 1)
                        save_link_to_db(save_name, save_url)
                        send_message(sender, f"✅ Đã lưu {save_name} với link: {save_url}")
                    except ValueError:
                        send_message(sender, "❌ Sai cú pháp! Dùng: /save <tên> <link>")

                elif text.startswith('/get '):
                    name = text[5:]
                    link = get_link(name)
                    if link:
                        send_message(sender, f"🔗 Link của {name} là: {link}")
                    else:
                        send_message(sender, f"❌ Không tìm thấy link cho {name}")

                elif text.startswith('/del '):
                    name = text[5:]
                    if get_link(name):
                        delete_link(name)
                        send_message(sender, f"🗑️ Đã xóa link của {name}")
                    else:
                        send_message(sender, f"❌ Không tìm thấy link để xóa cho {name}")
    return "ok", 200

def send_message(psid, message):
    url = f"https://graph.facebook.com/v17.0/me/messages?access_token=EAAffNumwM40BO9fetZCNa7FjvE7OnhY6Yxex2EYJRXiqRNDdbQiuyv2E9AsTjzepZCX21C1oyC0m436ZB5yFNZA9UffZCoqEWOnCQnODcWnr5W5ympocEsZBCqnqlZARdanZBl4Twnyp3dLZBnKCApVC0VS2IR7Bi9hMujnMIKmQMucOae4jikWutAKLJXGHFNAZBYlQZDZD"
    payload = {
        "recipient": {"id": psid},
        "message": {"text": message}
    }
    requests.post(url, json=payload)

# Run Flask server
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
