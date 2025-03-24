import socket
from threading import Thread
import json
import os

# File để lưu trữ thông tin người dùng
USER_FILE = "users.json"

# Hàm đọc dữ liệu từ file
def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as file:
            return json.load(file)
    return {}

# Hàm lưu dữ liệu vào file
def save_users(users):
    with open(USER_FILE, "w") as file:
        json.dump(users, file, indent=4)

# Đọc dữ liệu người dùng khi khởi động
users = load_users()

def handle_client(conn, addr):
    print(f"Kết nối từ: {addr}")
    try:
        # Nhận dữ liệu từ client
        data = conn.recv(1024).decode("utf-8")
        action, username, password = data.split(",")

        if action == "login":
            # Xử lý đăng nhập
            if username in users and users[username] == password:
                conn.send("Login successful".encode("utf-8"))
            else:
                conn.send("Login failed".encode("utf-8"))
        elif action == "register":
            # Xử lý đăng ký
            if username in users:
                conn.send("Register failed: Username already exists".encode("utf-8"))
            else:
                users[username] = password
                save_users(users)  # Lưu dữ liệu vào file
                conn.send("Register successful".encode("utf-8"))
        else:
            conn.send("Invalid action".encode("utf-8"))
    except Exception as e:
        print(f"Lỗi xử lý kết nối từ {addr}: {e}")
    finally:
        conn.close()

def server_program(host, port):
    serversocket = socket.socket()
    serversocket.bind((host, port))
    serversocket.listen(10)
    print(f"Listening on: {host}:{port}")

    while True:
        conn, addr = serversocket.accept()
        thread = Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    host = "0.0.0.0"  # Lắng nghe trên tất cả các địa chỉ IP
    port = 22236
    server_program(host, port)  