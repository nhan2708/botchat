from flask import Flask, request
import requests
import sqlite3
import os

app = Flask(__name__)

# Token xác minh và Page Access Token của bạn
VERIFY_TOKEN = "mytoken123"
PAGE_ACCESS_TOKEN = "EAAffNumwM40BO9fetZCNa7FjvE7OnhY6Yxex2EYJRXiqRNDdbQiuyv2E9AsTjzepZCX21C1oyC0m436ZB5yFNZA9UffZCoqEWOnCQnODcWnr5W5ympocEsZBCqnqlZARdanZBl4Twnyp3dLZBnKCApVC0VS2IR7Bi9hMujnMIKmQMucOae4jikWutAKLJXGHFNAZBYlQZDZD"

# Cấu hình database SQLite
db_path = os.environ.get('DATABASE_URL', 'links.db')  # Render sẽ tạo DATABASE_URL môi trường khi bạn tạo Persistent Volume
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()

# Tạo bảng nếu chưa có
cursor.execute("CREATE TABLE IF NOT EXISTS links (name TEXT, url TEXT)")
conn.commit()

def save_link_to_db(name, url):
    """Lưu link vào database"""
    try:
        cursor.execute("INSERT INTO links (name, url) VALUES (?, ?)", (name, url))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error saving link: {e}")
        return False
    return True

def get_link(name):
    """Lấy link từ database theo tên đã lưu"""
    cursor.execute("SELECT url FROM links WHERE name=?", (name,))
    result = cursor.fetchone()
    return result[0] if result else None

def delete_link(name):
    """Xóa link theo tên đã lưu"""
    cursor.execute("DELETE FROM links WHERE name=?", (name,))
    conn.commit()

@app.route("/webhook", methods=['GET'])
def verify():
    """Xác minh webhook với Facebook"""
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Verification failed", 403

@app.route("/webhook", methods=['POST'])
def webhook():
    """Xử lý tin nhắn nhận được từ Messenger"""
    data = request.get_json()
    for entry in data['entry']:
        for msg in entry['messaging']:
            if 'message' in msg:
                sender = msg['sender']['id']
                text = msg['message'].get('text', '')

                if text.startswith('/save '):  # Lưu link
                    try:
                        save_name, save_url = text[6:].split(' ', 1)
                        save_link_to_db(save_name, save_url)
                        send_message(sender, f"Đã lưu {save_name} với link: {save_url}")
                    except ValueError:
                        send_message(sender, "Sai cú pháp! Dùng: /save <tên> <link>")

                elif text.startswith('/get '):  # Lấy link
                    search_name = text[5:]
                    link = get_link(search_name)
                    if link:
                        send_message(sender, f"Link của {search_name} là: {link}")
                    else:
                        send_message(sender, f"Không tìm thấy link cho {search_name}")

                elif text.startswith('/del '):  # Xóa link
                    delete_name = text[5:]
                    if get_link(delete_name):  # Kiểm tra xem link có tồn tại không
                        delete_link(delete_name)  # Gọi hàm xóa
                        send_message(sender, f"Đã xóa link của {delete_name}")
                    else:
                        send_message(sender, f"Không tìm thấy link để xóa cho {delete_name}")

    return "ok", 200

def send_message(psid, message):
    """Gửi tin nhắn phản hồi về Messenger"""
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
