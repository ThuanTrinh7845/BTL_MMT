import socket
from threading import Thread
import time

hosted_channels = {}  # {channel_id: [(timestamp, author, content)]}
joined_channels = {}  # {channel_id: [(timestamp, author, content)]}
channel_peers = {} # {channel_id: [(ip, port)]}

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

def get_last_timestamp(channel_id):
    if channel_id in hosted_channels and hosted_channels[channel_id]:  # Kiểm tra kênh hosting
        return hosted_channels[channel_id][-1][0]
    elif channel_id in joined_channels and joined_channels[channel_id]:  # Kiểm tra kênh đã tham gia
        return joined_channels[channel_id][-1][0]
    else:
        return 0  # Trả về 0 nếu không có tin nhắn

def handle_incoming(conn, addr):
    data = conn.recv(1024).decode().strip()
    if data.startswith("JOIN_CHANNEL"):
        _, channel_id, peer_ip, peer_port = data.split()
        if channel_id in hosted_channels:
            if channel_id not in channel_peers:
                channel_peers[channel_id] = []
            channel_peers[channel_id].append((peer_ip, peer_port))  # Thêm một peer thuộc kênh channel_id vào channel_peers
            # history = " ".join([f"{t}:{a}:{m}" for t, a, m in hosted_channels[channel_id]])
            # print(history)
            # conn.send(f"CHANNEL_HISTORY {channel_id} {history}".encode())
    elif data.startswith("SEND_MESSAGE"):
        _, channel_id, username, message = data.split(" ", 3)
        if channel_id in joined_channels:
            joined_channels[channel_id].append((int(time.time()), username, message))
        if channel_id in hosted_channels:
            hosted_channels[channel_id].append((int(time.time()), username, message))
        print(f"message: {message}")
    conn.close()

def peer_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(10)
    print(f"Peer server listening on {host}:{port}")
    while True:
        conn, addr = server_socket.accept()
        Thread(target=handle_incoming, args=(conn, addr)).start()

def peer_client(tracker_ip, tracker_port, peer_ip, peer_port, username, session_id):
    # Đăng ký với tracker
    tracker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tracker.connect((tracker_ip, tracker_port))
    tracker.send(f"REGISTER {peer_ip} {peer_port} {username} {session_id} valid".encode())
    response = tracker.recv(1024).decode()
    print(response)

    # Tạo kênh (ví dụ)
    tracker.send("GET_PEER_LIST".encode())
    print(tracker.recv(1024).decode())

    # Vòng lặp CLI đơn giản
    while True:
        cmd = input("> ")
        if cmd.startswith("/join_channel"):
            _, channel_id = cmd.split()
            # tracker.send(f"GET_HOSTING_PEER {channel_id}".encode())
            # host_info = tracker.recv(1024).decode().split(" ")[1]
            # host_ip, host_port = host_info.split(":")
            # if host_ip != "offline":
            #     peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #     peer.connect((host_ip, int(host_port)))
            #     peer.send(f"JOIN_CHANNEL {channel_id} {peer_ip} {peer_port}".encode())
            #     history = peer.recv(1024).decode()
            #     if history.startswith("CHANNEL_HISTORY"):
            #         _, channel_id, *messages = history.split(" ")
            #         joined_channels[channel_id] = []
            #         if messages[0]:
            #             for msg in messages:
            #                 timestamp, author, content = msg.split(":")
            #                 joined_channels[channel_id].append(int(timestamp), author, content)
            #             print(f"Đã tham gia {channel_id}, lịch sử: {joined_channels[channel_id]}")
            #     else:
            #         print(history)
            #     peer.close()
            peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)                #
            peer.connect((tracker_ip, tracker_port))                                # Kết nối đến tracker để join vào một kênh
            peer.send(f"JOIN_CHANNEL {channel_id} {peer_ip} {peer_port}".encode())  #
            history = peer.recv(1024).decode()
            if history.startswith("CHANNEL_HISTORY"):
                _, channel_id, messages = history.split(" ",2)
                joined_channels[channel_id] = []
                # if messages[0]:
                #     for msg in messages:
                #         timestamp, author, content = msg.split(":")
                #         joined_channels[channel_id].append((int(timestamp), author, content))
                #     print(f"Đã tham gia {channel_id}, lịch sử: {joined_channels[channel_id]}")
                if messages:
                    message = messages.split(" ")
                    for msg in message:
                        print(msg)
                        timestamp, author, content = msg.split(":")
                        content = content.replace("_"," ")
                        joined_channels[channel_id].append((int(timestamp), author, content))
                    print(f"Đã tham gia {channel_id}, lịch sử: {joined_channels[channel_id]}")
            else:
                print(history)
            peer.close()

        elif cmd.startswith("/send_message"):
            parts = cmd.split(" ", 3)
            if len(parts) < 4:
                print("Syntax error")
                continue

            _, channel_id, username, message = parts
            # if channel_id in hosted_channels:  # Peer2 là hosting peer, thêm tin nhắn trực tiếp vào hosted_channels
            #     hosted_channels[channel_id].append((int(time.time()), username, message))
            # if channel_id in joined_channels:
            #     joined_channels[channel_id].append((int(time.time()), username, message))

            # tracker.send(f"GET_HOSTING_PEER {channel_id}".encode())
            # host_info = tracker.recv(1024).decode().split(" ")[1]
            # host_ip, host_port = host_info.split(":")
            # if host_ip != "offline":
            #     peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #     peer.connect((host_ip, int(host_port)))
            #     # Gửi lệnh SEND_MESSAGE
            #     peer.send(f"SEND_MESSAGE {channel_id} {username} {message}".encode())
            #     # response = peer.recv(1024).decode()
            #     # print(response)  # In ra phản hồi từ hosting peer, ví dụ: "MESSAGE_SENT"
            #     joined_channels[channel_id].append((int(time.time()), username, message))
            #     peer.close()
            peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)               #
            peer.connect((tracker_ip, tracker_port))                               # Kết nối đến tracker để gửi tin nhắn
            peer.send(f"SEND_MESSAGE {channel_id} {username} {message}".encode())  #
            peer.close()
        elif cmd.startswith("/sync_channel"):
            _, channel_id = cmd.split()
            last_timestamp = get_last_timestamp(channel_id)  # Lấy timestamp cuối, mặc định là 0 nếu chưa có
            peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer.connect((tracker_ip, tracker_port))  
            peer.send(f"SYNC_CHANNEL {channel_id} {last_timestamp}".encode())
            updates = tracker.recv(1024).decode()
            if updates.startswith("CHANNEL_UPDATES"):
                _, channel_id, messages_str = updates.split(" ",2)
                if messages_str:
                    messages = messages_str.split(" ")
                    for msg in messages:
                        timestamp, author, content = msg.split(":")
                        if channel_id in joined_channels:
                            joined_channels[channel_id].append((int(timestamp), author, content))
                        if channel_id in hosted_channels:
                            hosted_channels[channel_id].append((int(timestamp), author, content))
                    print(f"Đã đồng bộ {channel_id}")
        else:
            print("Lệnh không hợp lệ!")

if __name__ == "__main__":
    peer_ip = get_host_ip()
    peer_port = 33358
    tracker_ip = "192.168.1.5"  # Thay bằng IP thực tế
    tracker_port = 22236
    username = "user2"
    session_id = "sid2"
    
    Thread(target=peer_server, args=(peer_ip, peer_port)).start()
    peer_client(tracker_ip, tracker_port, peer_ip, peer_port, username, session_id)