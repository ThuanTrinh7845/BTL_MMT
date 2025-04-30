import socket
import queue
import json
from threading import Thread
import time
from tkinter import messagebox
import cv2
import pyaudio
import pickle
import struct
from PIL import Image, ImageTk
import numpy as np

class PeerClient:
    def __init__(self, tracker_ip, tracker_port, peer_ip, peer_port, username=None, password=None, is_visitor=False):
        self.tracker_ip = tracker_ip
        self.tracker_port = tracker_port
        self.peer_ip = peer_ip
        self.peer_port = peer_port
        self.is_visitor = is_visitor
        self.username = username
        self.password = password
        self.message_queue = queue.Queue()
        self.channel_peers = {}
        self.server_socket = None
        self.channel_id = None
        self.streaming = False
        self.stream_sockets = []
        self.stream_thread = None
        self.video_queues = {}        #{channel_id: queue.Queue(maxsize=20)}
        self.audio_queue = queue.Queue(maxsize=50)
        self.audio_stream = None
        self.p = pyaudio.PyAudio()
        self.audio_format = pyaudio.paInt16
        self.audio_channels = 1
        self.audio_rate = 44100
        self.audio_chunk_size = 2048
        self.audio_gain = 2.0

    def save_hosted_channels(self, filename='peer1_hosted_channels.json'):
        with open(filename, 'w') as f:
            json.dump(self.hosted_channels, f)

    def save_joined_channels(self, filename='peer1_joined_channels.json'):
        with open(filename, 'w') as f:
            json.dump(self.joined_channels, f)

    def load_hosted_channels(self, filename='peer1_hosted_channels.json'):
        try:
            with open(filename, 'r') as f:
                content = f.read()
                if content:
                    self.hosted_channels = json.loads(content)
                else:
                    self.hosted_channels = {}
        except (FileNotFoundError, json.JSONDecodeError):
            self.hosted_channels = {}

    def load_joined_channels(self, filename='peer1_joined_channels.json'):
        try:
            with open(filename, 'r') as f:
                content = f.read()
                if content:
                    self.joined_channels = json.loads(content)
                else:
                    self.joined_channels = {}
        except (FileNotFoundError, json.JSONDecodeError):
            self.joined_channels = {}

    def get_host_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.1'
        finally:
            s.close()
        return ip

    def get_last_timestamp(self, channel_id):
        if channel_id in self.hosted_channels and self.hosted_channels[channel_id]:
            return self.hosted_channels[channel_id][-1][0]
        elif channel_id in self.joined_channels and self.joined_channels[channel_id]:
            return self.joined_channels[channel_id][-1][0]
        return 0

    # Hàm handle_incoming được sửa
    def handle_incoming(self, conn, addr):
        try:
            # Nhận dữ liệu thô (không decode ngay)
            raw_data = conn.recv(1024)
            if not raw_data:
                conn.close()
                return
            
            # Thử decode dữ liệu thành UTF-8 để kiểm tra lệnh văn bản
            try:
                data = raw_data.decode('utf-8').strip()
                print(f"Nhận từ {addr}: {data}")
                
                if data.startswith("JOIN_CHANNEL"):
                    _, channel_id, peer_ip, peer_port = data.split()
                    if channel_id in self.hosted_channels:
                        if channel_id not in self.channel_peers:
                            self.channel_peers[channel_id] = []
                        self.channel_peers[channel_id].append((peer_ip, int(peer_port)))
                elif data.startswith("SEND_MESSAGE"):
                    _, channel_id, username, message = data.split(" ", 3)
                    if channel_id in self.joined_channels:
                        self.joined_channels[channel_id].append((int(time.time()), username, message))
                        self.save_joined_channels()
                    if channel_id in self.hosted_channels:
                        self.hosted_channels[channel_id].append((int(time.time()), username, message))
                        self.save_hosted_channels()
                    self.message_queue.put((channel_id, username, message))
                elif data.startswith("STREAM_START"):
                    _, self.channel_id = data.split()
                    print(f"Bắt đầu nhận stream từ {addr}")
                    # Thread(target=self.receive_stream, args=(conn, channel_id)).start()
                    return  # Thoát để receive_stream xử lý dữ liệu binary tiếp theo
                else:
                    conn.close()
            except UnicodeDecodeError:
                # Nếu không decode được (dữ liệu binary), giả định là stream và chuyển sang receive_stream
                print(f"Nhận dữ liệu binary từ {addr}, chuyển sang receive_stream")
                Thread(target=self.receive_stream, args=(conn, self.channel_id)).start()
                return
        except Exception as e:
            print(f"Lỗi trong handle_incoming từ {addr}: {e}")
            conn.close()

    def peer_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.peer_ip, self.peer_port))
        self.server_socket.listen(10)
        print(f"Peer server listening on {self.peer_ip}:{self.peer_port}")
        while True:
            conn, addr = self.server_socket.accept()
            Thread(target=self.handle_incoming, args=(conn, addr)).start()

    def register_visitor_with_tracker(self, nickname):
        tracker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tracker.connect((self.tracker_ip, self.tracker_port))
        tracker.send(f"VISITOR {self.peer_ip} {self.peer_port} {nickname}".encode())
        response = tracker.recv(1024).decode()
        tracker.close()
        return response

    def register_with_tracker(self, username, password):
        tracker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tracker.connect((self.tracker_ip, self.tracker_port))
        tracker.send(f"REGISTER {self.peer_ip} {self.peer_port} {username} {password}".encode())
        response = tracker.recv(1024).decode()
        tracker.close()
        return response

    def login_with_tracker(self, username, password):
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

    def set_channel_privacy(self, channel_id, privacy):
        """Gửi yêu cầu đến tracker để đặt trạng thái private/public"""
        if channel_id not in self.hosted_channels:
            return False
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.tracker_ip, self.tracker_port))
            request = f"SET_CHANNEL_PRIVACY {channel_id} {privacy}"
            sock.send(request.encode())
            response = sock.recv(1024).decode()
            sock.close()
            return response == "SUCCESS"
        except Exception as e:
            print(f"Lỗi khi đặt trạng thái kênh: {e}")
            return False
        
    def get_channel_privacy(self, channel_id):
        """Lấy trạng thái private/public từ tracker"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.tracker_ip, self.tracker_port))
            request = f"GET_CHANNEL_PRIVACY {channel_id}"
            sock.send(request.encode())
            response = sock.recv(1024).decode()
            sock.close()
            return response  # "private" hoặc "public"
        except Exception as e:
            print(f"Lỗi khi lấy trạng thái kênh: {e}")
            return "public"  # Mặc định public nếu lỗi

    def can_visitor_view(self, channel_id):
        """Kiểm tra xem visitor có được xem kênh không"""
        privacy = self.get_channel_privacy(channel_id)
        return privacy == "public"

    def create_channel(self, channel_id):
        try:
            peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer.connect((self.tracker_ip, self.tracker_port))
            request = f"CREATE_CHANNEL {channel_id} {self.username}"
            print(f"Gửi yêu cầu tạo kênh: {request}")
            peer.send(request.encode())
            response = peer.recv(1024).decode()
            print(f"Nhận phản hồi từ tracker: {response}")
            peer.close()
            if response == "CHANNEL_CREATED":
                self.hosted_channels[channel_id] = []
                self.save_hosted_channels()
                print(f"Kênh {channel_id} được tạo thành công")
                return True
            else:
                print(f"Tạo kênh thất bại: {response}")
                return False
        except Exception as e:
            print(f"Lỗi khi tạo kênh: {e}")
            return False

    def search_channels(self, keyword):
        try:
            tracker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tracker.connect((self.tracker_ip, self.tracker_port))
            tracker.send(f"SEARCH_CHANNEL {keyword}".encode())
            response = tracker.recv(1024).decode()
            tracker.close()
            if response.startswith("CHANNEL_LIST"):
                _, *channels = response.split()
                return channels
            return []
        except Exception as e:
            print(f"Lỗi khi tìm kiếm kênh: {e}")
            return []
        
    def get_content_channel_id(self, channel_id):
        try:
            peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer.connect((self.tracker_ip, self.tracker_port))
            peer.send(f"GET_MESSAGE {channel_id} {self.peer_ip} {self.peer_port}".encode())
            history = peer.recv(1024).decode()
            peer.close()
            if history.startswith("CHANNEL_HISTORY"):
                _, channel_id, messages_str = history.split(" ", 2)
                channel_for_visitor = []
                if messages_str:
                    messages = messages_str.split(" ")
                    for msg in messages:
                        timestamp, author, content = msg.split(":")
                        content = content.replace("_", " ")
                        channel_for_visitor.append((int(timestamp), author, content))
                return channel_for_visitor
            return []
        except Exception as e:
            print(f"Lỗi khi lấy tin nhắn từ tracker: {e}")
            return []

    def join_channel(self, channel_id):
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
                return True
            return False
        except Exception as e:
            print(f"Lỗi khi tham gia kênh: {e}")
            return False

    def send_message(self, channel_id, message):
        peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer.connect((self.tracker_ip, self.tracker_port))
        peer.send(f"SEND_MESSAGE {channel_id} {self.username} {message}".encode())
        peer.close()

    def sync_channel(self, channel_id):
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
        peer.close()

    def get_channel_peers(self, channel_id):
        peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer.connect((self.tracker_ip, self.tracker_port))
        peer.send(f"GET_CHANNEL_PEERS {channel_id}".encode())
        response = peer.recv(1024).decode()
        peer.close()
        if response.startswith("CHANNEL_PEERS"):
            _, _, peers_str = response.split(" ", 2)
            return [tuple(peer.split(":")) for peer in peers_str.split()]
        return []

    def start_stream(self, channel_id):
        self.streaming = True
        peers = self.get_channel_peers(channel_id)
        self.stream_sockets = []
        for peer_ip, peer_port in peers:
            if (peer_ip, int(peer_port)) != (self.peer_ip, self.peer_port):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((peer_ip, int(peer_port)))
                    sock.send(f"STREAM_START {channel_id}".encode())
                    sock.close()

                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    # sock.settimeout(10)
                    sock.connect((peer_ip, int(peer_port)))
                    self.stream_sockets.append(sock)
                    print(f"Kết nối stream tới {peer_ip}:{peer_port}")
                except Exception as e:
                    print(f"Không thể kết nối tới {peer_ip}:{peer_port}: {e}")
        
        init_signal = pickle.dumps("START")
        init_packet = bytes([3]) + struct.pack("L", len(init_signal)) + init_signal
        for sock in self.stream_sockets[:]:
            try:
                sock.sendall(init_packet)
            except Exception as e:
                print(f"Lỗi gửi tín hiệu khởi động đến {sock.getpeername()}: {e}")
                self.stream_sockets.remove(sock)

        self.stream_thread = Thread(target=self.send_stream, args=(channel_id,))
        self.stream_thread.start()

    def stop_stream(self, channel_id):
        self.channel_id = None
        self.streaming = False
        stop_signal = pickle.dumps(None)
        stop_packet = bytes([2]) + struct.pack("L", len(stop_signal)) + stop_signal
        for sock in self.stream_sockets[:]:
            try:
                sock.sendall(stop_packet)
                sock.close()
            except Exception as e:
                print(f"Lỗi gửi tín hiệu dừng đến {sock.getpeername()}: {e}")
            self.stream_sockets.remove(sock)
        self.stream_sockets = []
        if self.stream_thread:
            self.stream_thread.join()
        if channel_id in self.video_queues:
            while not self.video_queues[channel_id].empty():
                self.video_queues[channel_id].get()
            # self.video_queues[channel_id].put(None)
        del self.video_queues[channel_id]
        while not self.audio_queue.empty():
            self.audio_queue.get()
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None
        # self.video_queue.put(None)
        print("Stream đã dừng")

    def send_stream(self, channel_id):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Lỗi: Không thể mở webcam")
            return
        audio_stream = self.p.open(
            format=self.audio_format,
            channels=self.audio_channels,
            rate=self.audio_rate,
            input=True,
            frames_per_buffer=self.audio_chunk_size
        )
        print("Bắt đầu gửi stream")
        while self.streaming:
            ret, frame = cap.read()
            if not ret:
                print("Lỗi: Không thể đọc frame từ webcam")
                break
            # if not self.video_queue.full():
            #     self.video_queue.put(frame)
            if channel_id not in self.video_queues:
                self.video_queues[channel_id] = queue.Queue(maxsize=20)
            if not self.video_queues[channel_id].full():
                self.video_queues[channel_id].put(frame)
            
            video_data = pickle.dumps(frame)
            video_packet = bytes([0]) + struct.pack("L", len(video_data)) + video_data
            
            audio_chunk = audio_stream.read(self.audio_chunk_size, exception_on_overflow=False)
            audio_array = np.frombuffer(audio_chunk, dtype=np.int16)
            amplified_audio = (audio_array * self.audio_gain).clip(-32768, 32767).astype(np.int16)
            audio_data = pickle.dumps(amplified_audio.tobytes())
            audio_packet = bytes([1]) + struct.pack("L", len(audio_data)) + audio_data

            for sock in self.stream_sockets[:]:
                try:
                    sock.sendall(video_packet)
                    sock.sendall(audio_packet)
                except Exception as e:
                    print(f"Lỗi gửi đến {sock.getpeername()}: {e}")
                    self.stream_sockets.remove(sock)
            time.sleep(0.03)
        cap.release()
        audio_stream.stop_stream()
        audio_stream.close()
        print("Đã ngừng gửi stream")

    def receive_stream(self, conn, channel_id):
        data = b""
        header_size = 5
        conn.settimeout(10)
        print("Đang nhận stream...")
        while True:
            try:
                while len(data) < header_size:
                    packet = conn.recv(4096)
                    if not packet:
                        print("Socket từ host đã đóng")
                        break
                    data += packet
                if len(data) < header_size:
                    break
                data_type = data[0]
                packed_size = data[1:header_size]
                data = data[header_size:]
                msg_size = struct.unpack("L", packed_size)[0]

                while len(data) < msg_size:
                    packet = conn.recv(4096)
                    if not packet:
                        print("Socket từ host đóng giữa chừng")
                        break
                    data += packet
                payload_data = data[:msg_size]
                data = data[msg_size:]

                if data_type == 3:
                    signal = pickle.loads(payload_data)
                    if signal == "START":
                        print("Streamer đã bắt đầu stream")
                    continue
                elif data_type == 2:
                    frame = pickle.loads(payload_data)
                    if frame is None:
                        if channel_id in self.video_queues:
                            while not self.video_queues[channel_id].empty():
                                self.video_queues[channel_id].get()
                            self.video_queues[channel_id].put(None)
                        while not self.audio_queue.empty():
                            self.audio_queue.get()
                        # self.video_queues.put(None)
                        if self.audio_stream:
                            self.audio_stream.stop_stream()
                            self.audio_stream.close()
                            self.audio_stream = None
                        print("Nhận tín hiệu dừng từ host")
                        break
                elif data_type == 0:
                    frame = pickle.loads(payload_data)
                    if channel_id not in self.video_queues:
                        self.video_queues[channel_id] = queue.Queue(maxsize=20)
                    if not self.video_queues[channel_id].full():
                        self.video_queues[channel_id].put(frame)
                elif data_type == 1:
                    audio_data = pickle.loads(payload_data)
                    if not self.audio_queue.full():
                        self.audio_queue.put(audio_data)
                    if not self.audio_stream:
                        self.audio_stream = self.p.open(
                            format=self.audio_format,
                            channels=self.audio_channels,
                            rate=self.audio_rate,
                            output=True,
                            frames_per_buffer=self.audio_chunk_size
                        )
                    if not hasattr(self, 'audio_thread') or not self.audio_thread.is_alive():
                        self.audio_thread = Thread(target=self.play_audio, daemon=True)
                        self.audio_thread.start()
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Lỗi nhận dữ liệu: {e}")
                break
        conn.close()
        del self.video_queues[channel_id]
        print("Đã ngừng nhận stream")

    def play_audio(self):
        while self.audio_stream:
            try:
                if not self.audio_queue.empty():
                    audio_data = self.audio_queue.get()
                    if audio_data:
                        self.audio_stream.write(audio_data)
            except Exception as e:
                print(f"Lỗi phát âm thanh: {e}")
                time.sleep(0.01)

    def start(self):
        Thread(target=self.peer_server).start()
        self.load_hosted_channels()
        self.load_joined_channels()
        for channel_id in self.hosted_channels:
            self.sync_channel(channel_id)
        for channel_id in self.joined_channels:
            self.sync_channel(channel_id)