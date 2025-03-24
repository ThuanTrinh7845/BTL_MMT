import socket
from tkinter import messagebox

class Client:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port

    def call_server(self, action, username, password):
        """Gọi server để đăng nhập hoặc đăng ký"""
        try:
            client_socket = socket.socket()
            client_socket.connect((self.server_ip, self.server_port))
            client_socket.send(f"{action},{username},{password}".encode("utf-8"))
            response = client_socket.recv(1024).decode("utf-8")
            client_socket.close()
            return response
        except Exception as e:
            messagebox.showerror("Connection Error", f"Lỗi kết nối đến server: {e}")
            return None