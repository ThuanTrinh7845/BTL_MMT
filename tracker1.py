import socket
from threading import Thread
import time
import json
import os

# peer_list = [("192.168.1.5", 33359, "456", "sid3"), 
#              ("192.168.1.5", 33357, "123", "sid1")]        # [(ip, port, username, session_id)]
# channel_hosting = {"channel3":("192.168.1.5", 33359),
#                    "channel1":("192.168.1.5", 33357)}  # {channel_id: (ip, port)}
# channel_data = {"channel3":[],"channel1":[]}     # {channel_id: [(timestamp, author, content)]}
# channel_peers = {"channel3":[("192.168.1.5",33359),("192.168.1.5",33357)], 
#                  "channel1":[("192.168.1.5",33359),("192.168.1.5",33357)]}    # {channel_peers: [(ip,port)]}

peer_list = []
channel_hosting = {}
channel_data = {}
channel_peers = {}

def get_host_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

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

def broadcast_message(channel_id, author, message):
    # Gửi tin nhắn đến các peer trong kênh
    if channel_id in channel_peers:
        for peer_ip, peer_port in channel_peers[channel_id]:
            try:
                peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                peer_socket.connect((peer_ip, int(peer_port)))
                peer_socket.send(f"SEND_MESSAGE {channel_id} {author} {message}".encode())
                peer_socket.close()
            except Exception as e:
                print(f"Không thể gửi tin nhắn đến {peer_ip}:{peer_port}: {e}")

def broadcast_join_peer(channel_id):
    if channel_id in channel_peers:
        for peer_ip, peer_port in channel_peers[channel_id]:
            try:
                peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                peer_socket.connect((peer_ip, int(peer_port)))
                peer_socket.send(f"JOIN_CHANNEL {channel_id} {peer_ip} {peer_port}".encode())
                peer_socket.close()
            except Exception as e:
                print(f"Không thể gửi thông tin peer đến {peer_ip}:{peer_port}: {e}")

def handle_peer(conn, addr):
    while True:
        try:
            data = conn.recv(1024).decode().strip()
            if data.startswith("LOGIN"):
                _, username, password = data.split()
                if username in users and users[username] == password:
                    conn.send("Login successful".encode("utf-8"))
                else:
                    conn.send("Login failed".encode("utf-8"))
            # if data.startswith("register"):
            #     _, ip, port, username, session_id, password = data.split()
            #     if username in users:
            #         conn.send("Register failed: Username already exists".encode("utf-8"))
            #     else:
            #         users[username] = password
            #         save_users(users)  # Lưu dữ liệu vào file
            #         peer_list.append((ip, port, username, session_id))
            #         conn.send("Register successful".encode("utf-8"))
            if data.startswith("REGISTER"):
                _, ip, port, username, password, session_id = data.split()
                if username in users:
                    conn.send("Register failed: Username already exists".encode("utf-8"))
                else:
                    users[username] = password
                    save_users(users)  # Lưu dữ liệu vào file
                    peer_list.append((ip, port, username, session_id))
                    conn.send("Register successful".encode())
            elif data.startswith("GET_PEER_LIST"):
                response = "PEER_LIST " + " ".join([f"{ip}:{port}:{user}:{sid}" for ip, port, user, sid in peer_list])
                conn.send(response.encode())
            elif data.startswith("CREATE_CHANNEL"):
                print(peer_list)
                _, channel_id, username, session_id = data.split()
                hosting_peer = next((p for p in peer_list if p[2] == username and p[3] == session_id), None)
                if hosting_peer:
                    channel_hosting[channel_id] = [(hosting_peer[0], hosting_peer[1])]   
                    channel_peers[channel_id] = [(hosting_peer[0], hosting_peer[1])]  # Thêm một peer thuộc kênh channel_id vào channel_peers để broadcast
                    print(channel_hosting)
                    channel_data[channel_id] = []
                    conn.send("CHANNEL_CREATED".encode())
                else:
                    conn.send("CHANNEL_CREATE_FAIL".encode())
            elif data.startswith("GET_HOSTING_PEER"):
                _, channel_id = data.split()
                host = channel_hosting.get(channel_id, ("offline", "0"))
                conn.send(f"HOSTING_PEER {host[0]}:{host[1]}".encode())
            elif data.startswith("SYNC_CHANNEL"):
                _, channel_id, last_timestamp = data.split()
                if channel_id in channel_data:
                    updates = [msg for msg in channel_data[channel_id] if msg[0] > int(last_timestamp)]
                    updates_str = " ".join([f"{t}:{a}:{m.replace(' ', '_')}" for t, a, m in updates])
                    conn.send(f"CHANNEL_UPDATES {channel_id} {updates_str}".encode())
                else:
                    conn.send(f"CHANNEL_UPDATE {channel_id}".encode())
            elif data.startswith("JOIN_CHANNEL"):
                _, channel_id, peer_ip, peer_port = data.split()
                if channel_id in channel_data:
                    if channel_id not in channel_peers:
                        channel_peers[channel_id] = []
                    channel_peers[channel_id].append((peer_ip, peer_port))  # Thêm một peer thuộc kênh channel_id vào channel_peers để broadcast
                    broadcast_join_peer(channel_id)              # Gửi thông tin peer mới tham gia vào kênh cho hosting_peer
                    history = " ".join([f"{t}:{a}:{m.replace(' ','_')}" for t, a, m in channel_data[channel_id]])
                    print(history)
                    conn.send(f"CHANNEL_HISTORY {channel_id} {history}".encode())
            elif data.startswith("SEARCH_CHANNEL"):
                parts = data.split(" ", 1)
                if len(parts) < 2:
                    response = "ERROR: Missing keyword"
                else:
                    keyword = parts[1].lower()
                    matching_channels = [channel_id for channel_id in channel_hosting.keys() if keyword in channel_id.lower()]
                    if matching_channels:
                        response = "CHANNEL_LIST " + " ".join(matching_channels)
                    else:
                        response = "NO_CHANNEL_FOUND"
                conn.send(response.encode())
                    
            elif data.startswith("SEND_MESSAGE"):
                _, channel_id, username, message = data.split(" ", 3)
                if channel_id in channel_data:
                    timestamp = int(time.time())
                    channel_data[channel_id].append((timestamp, username, message))
                    broadcast_message(channel_id, username, message)  # Broadcast cho các peer trong kênh channel_id
                    print(f"message: {message}")
        except Exception:
            # peer_list.remove(next(p for p in peer_list if p[0] == addr[0] and p[1] == str(addr[1])))
            # peer_to_remove = next((p for p in peer_list if p[0] == addr[0] and p[1] == str(addr[1])), None)
            # if peer_to_remove:
            #     peer_list.remove(peer_to_remove)
            conn.close()
            break
    conn.close()

def tracker_program(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(10)
    print(f"Tracker listening on {host}:{port}")
    while True:
        conn, addr = server_socket.accept()
        Thread(target=handle_peer, args=(conn, addr)).start()

if __name__ == "__main__":
    host = "10.229.5.204"
    port = 22236
    tracker_program(host, port)