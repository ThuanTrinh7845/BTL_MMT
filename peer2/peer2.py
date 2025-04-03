import socket
import queue
import json
from threading import Thread
import time
from tkinter import messagebox

class PeerClient:
    def __init__(self, tracker_ip, tracker_port, peer_ip, peer_port, username, password, session_id):
        """Khởi tạo PeerClient với thông tin tracker và peer"""
        self.tracker_ip = tracker_ip
        self.tracker_port = tracker_port
        self.peer_ip = peer_ip
        self.peer_port = peer_port
        self.username = username
        self.password = password
        self.session_id = session_id
        # self.hosted_channels = {"channel3": []}  # {channel_id: [(timestamp, author, content)]}
        # self.joined_channels = {"channel1": []}  # {channel_id: [(timestamp, author, content)]}
        self.message_queue = queue.Queue()
        self.channel_peers = {}    # {channel_id: [(ip, port)]}
        self.server_socket = None

    def save_hosted_channels(self, filename='peer2_hosted_channels.json'):
        """Lưu hosted_channels vào file JSON"""
        with open(filename, 'w') as f:
            json.dump(self.hosted_channels, f)

    def save_joined_channels(self, filename='peer2_joined_channels.json'):
        """Lưu joined_channels vào file JSON"""
        with open(filename, 'w') as f:
            json.dump(self.joined_channels, f)

    def load_hosted_channels(self, filename='peer2_hosted_channels.json'):
        """Tải hosted_channels từ file JSON"""
        try:
            with open(filename, 'r') as f:
                content = f.read()
                if content:
                    self.hosted_channels = json.loads(content)
                else:
                    self.hosted_channels = {}
        except (FileNotFoundError, json.JSONDecodeError):
            self.hosted_channels = {}  # Giá trị mặc định

    def load_joined_channels(self, filename='peer2_joined_channels.json'):
        """Tải joined_channels từ file JSON"""
        try:
            with open(filename, 'r') as f:
                content = f.read()
                if content:
                    self.joined_channels = json.loads(content)
                else:
                    self.joined_channels = {}
        except (FileNotFoundError, json.JSONDecodeError):
            self.joined_channels = {}  # Giá trị mặc định

    def get_host_ip(self):
        """Lấy địa chỉ IP của host"""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    def get_last_timestamp(self, channel_id):
        """Lấy timestamp cuối cùng của kênh"""
        if channel_id in self.hosted_channels and self.hosted_channels[channel_id]:
            return self.hosted_channels[channel_id][-1][0]
        elif channel_id in self.joined_channels and self.joined_channels[channel_id]:
            return self.joined_channels[channel_id][-1][0]
        return 0

    def handle_incoming(self, conn, addr):
        """Xử lý kết nối từ các peer khác"""
        data = conn.recv(1024).decode().strip()
        if data.startswith("JOIN_CHANNEL"):
            _, channel_id, peer_ip, peer_port = data.split()
            if channel_id in self.hosted_channels:
                if channel_id not in self.channel_peers:
                    self.channel_peers[channel_id] = []
                self.channel_peers[channel_id].append((peer_ip, peer_port))
        elif data.startswith("SEND_MESSAGE"):
            _, channel_id, username, message = data.split(" ", 3)
            if channel_id in self.joined_channels:
                self.joined_channels[channel_id].append((int(time.time()), username, message))
                self.save_joined_channels()
            if channel_id in self.hosted_channels:
                self.hosted_channels[channel_id].append((int(time.time()), username, message))
                self.save_hosted_channels()
            print(f"message: {message}")
            self.message_queue.put((channel_id, username, message))
        conn.close()

    def peer_server(self):
        """Khởi động server peer để lắng nghe kết nối từ peer khác"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.peer_ip, self.peer_port))
        self.server_socket.listen(10)
        print(f"Peer server listening on {self.peer_ip}:{self.peer_port}")
        while True:
            conn, addr = self.server_socket.accept()
            Thread(target=self.handle_incoming, args=(conn, addr)).start()

    def register_with_tracker(self, username, password):
        """Đăng ký với tracker"""
        tracker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tracker.connect((self.tracker_ip, self.tracker_port))
        tracker.send(f"REGISTER {self.peer_ip} {self.peer_port} {username} {password} {self.session_id}".encode())
        response = tracker.recv(1024).decode()
        tracker.close()
        return response

    def login_with_tracker(self, username, password):
        """Gọi server để đăng nhập hoặc đăng ký"""
        try:
            peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer.connect((self.tracker_ip, self.tracker_port))
            peer.send(f"LOGIN {username} {password}".encode("utf-8"))
            response = peer.recv(1024).decode("utf-8")
            peer.close()
            return response
        except Exception as e:
            messagebox.showerror("Connection Error", f"Lỗi kết nối đến server: {e}")
            return None

    def create_channel(self, channel_id):
        """Tạo một kênh mới thông qua tracker"""
        try:
            peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer.connect((self.tracker_ip, self.tracker_port))
            peer.send(f"CREATE_CHANNEL {channel_id} {self.username} {self.session_id}".encode())
            response = peer.recv(1024).decode()
            peer.close()
            # Kiểm tra phản hồi
            if response == "CHANNEL_CREATED":
                self.hosted_channels[channel_id] = []
                print(f"Kênh {channel_id} đã được tạo thành công.")
                return True
            else:
                print(f"Tạo kênh {channel_id} thất bại: {response}")
                return False
        except Exception as e:
            print(f"Lỗi khi tạo kênh: {e}")
            return False
        
    def search_channels(self, keyword):
        """Gửi yêu cầu tìm kiếm kênh đến tracker và nhận danh sách kênh khớp"""
        try:
            tracker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tracker.connect((self.tracker_ip, self.tracker_port))
            tracker.send(f"SEARCH_CHANNEL {keyword}".encode())
            response = tracker.recv(1024).decode()
            tracker.close()
            if response.startswith("CHANNEL_LIST"):
                _, *channels = response.split()
                return channels
            else:
                print(f"Tìm kiếm thất bại")
                return []
        except Exception as e:
            print(f"Lỗi khi tìm kiếm kênh: {e}")
            return []

    def join_channel(self, channel_id):
        """Tham gia kênh qua tracker"""
        try:
            peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer.connect((self.tracker_ip, self.tracker_port))
            peer.send(f"JOIN_CHANNEL {channel_id} {self.peer_ip} {self.peer_port}".encode())
            history = peer.recv(1024).decode()
            peer.close()
            if history.startswith("CHANNEL_HISTORY"):
                _, channel_id, messages_str = history.split(" ", 2)
                self.joined_channels[channel_id] = []
                if messages_str:
                    messages = messages_str.split(" ")
                    for msg in messages:
                        timestamp, author, content = msg.split(":")
                        content = content.replace("_", " ")
                        self.joined_channels[channel_id].append((int(timestamp), author, content))
                        self.save_joined_channels()
                    print(f"Đã tham gia {channel_id}, lịch sử: {self.joined_channels[channel_id]}")
                return True
            else:
                return False
        except Exception as e:
            return False

    def send_message(self, channel_id, message):
        """Gửi tin nhắn đến kênh qua tracker"""
        peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer.connect((self.tracker_ip, self.tracker_port))
        peer.send(f"SEND_MESSAGE {channel_id} {self.username} {message}".encode())
        peer.close()

    def sync_channel(self, channel_id):
        """Đồng bộ kênh với tracker"""
        last_timestamp = self.get_last_timestamp(channel_id)
        peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer.connect((self.tracker_ip, self.tracker_port))
        peer.send(f"SYNC_CHANNEL {channel_id} {last_timestamp}".encode())
        updates = peer.recv(1024).decode()
        if updates.startswith("CHANNEL_UPDATES"):
            _, channel_id, messages_str = updates.split(" ", 2)
            if messages_str:
                messages = messages_str.split(" ")
                for msg in messages:
                    timestamp, author, content = msg.split(":")
                    content = content.replace("_", " ")
                    if channel_id in self.joined_channels:
                        self.joined_channels[channel_id].append((int(timestamp), author, content))
                        self.save_joined_channels()
                    if channel_id in self.hosted_channels:
                        self.hosted_channels[channel_id].append((int(timestamp), author, content))
                        self.save_hosted_channels()
                print(f"Đã đồng bộ {channel_id}")
        peer.close()

    def run_cli(self):
        """Chạy giao diện dòng lệnh cho peer"""
        while True:
            cmd = input("> ")
            if cmd.startswith("/join_channel"):
                _, channel_id = cmd.split()
                self.join_channel(channel_id)
            elif cmd.startswith("/send_message"):
                parts = cmd.split(" ", 3)
                if len(parts) < 4:
                    print("Syntax error")
                    continue
                _, channel_id, _, message = parts
                self.send_message(channel_id, message)
            elif cmd.startswith("/sync_channel"):
                _, channel_id = cmd.split()
                self.sync_channel(channel_id)
            else:
                print("Lệnh không hợp lệ!")

    def start(self):
        """Khởi động peer: đăng ký, chạy server và CLI"""
        # self.register_with_tracker()
        Thread(target=self.peer_server).start()
        self.load_hosted_channels()
        self.load_joined_channels()
        for channel_id in self.hosted_channels:
            self.sync_channel(channel_id)
        for channel_id in self.joined_channels:
            self.sync_channel(channel_id)
        # self.run_cli()
