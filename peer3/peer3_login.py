import tkinter as tk
from tkinter import messagebox
import socket
import threading
from peer3 import PeerClient

class Peer3LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Peer3 Login")
        self.root.geometry("300x200")

        # Cấu hình server (tracker)
        self.server_ip = "192.168.1.2"  # Địa chỉ IP của tracker
        self.server_port = 22236     # Cổng của tracker

        self.peer_client = None

        # Tạo các thành phần UI
        self.create_login_ui()

    def get_host_ip(self):
        return socket.gethostbyname(socket.gethostname())

    def create_login_ui(self):
        tk.Label(self.root, text="Username:").pack(pady=5)
        self.username_entry = tk.Entry(self.root)
        self.username_entry.pack(pady=5)

        tk.Label(self.root, text="Password:").pack(pady=5)
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.pack(pady=5)

        tk.Button(self.root, text="Login", command=self.attempt_login).pack(pady=10)
        tk.Button(self.root, text="Register", command=self.attempt_register).pack(pady=10)
        tk.Button(self.root, text="Visitor Mode", command=self.enter_visitor_mode).pack(pady=10)

    def attempt_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        # Khởi tạo PeerClient cho peer1
        self.peer_client = PeerClient(self.server_ip, self.server_port, self.get_host_ip(), 33359, username=username, password=password, is_visitor=False)
        response = self.peer_client.login_with_tracker(username, password)  # Đăng nhập với tracker
        print(response)
        if response == "Login successful":
            threading.Thread(target=self.peer_client.start).start()
            messagebox.showinfo("Login Success", "Đăng nhập thành công!")
            self.root.destroy()
            self.open_main_app(username)
        else:
            messagebox.showerror("Login Failed", "Tên đăng nhập hoặc mật khẩu không đúng!")

    def attempt_register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        self.peer_client = PeerClient(self.server_ip, self.server_port, self.get_host_ip(), 33359, username=username, password=password, is_visitor=False)

        # Gọi server để đăng ký
        response = self.peer_client.register_with_tracker(username, password)

        if response == "Register successful":
            messagebox.showinfo("Register Success", "Đăng ký thành công!")
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Register Failed", "Username đã tồn tại!")
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)

    def enter_visitor_mode(self):
        """Chuyển sang chế độ visitor"""
        # Tạo cửa sổ Toplevel
        nickname_window = tk.Toplevel(self.root)
        nickname_window.title("Visitor Mode - Nhập Nickname")
        nickname_window.geometry("250x150")
        nickname_window.transient(self.root)  # Đặt cửa sổ phụ thuộc vào cửa sổ chính
        nickname_window.grab_set()  # Chặn tương tác với cửa sổ chính

        # Nhãn và ô nhập nickname
        tk.Label(nickname_window, text="Nhập nickname:").pack(pady=10)
        nickname_entry = tk.Entry(nickname_window)
        nickname_entry.pack(pady=5)
        nickname_entry.focus_set()  # Đặt con trỏ vào ô nhập

        def confirm_nickname():
            nickname = nickname_entry.get().strip()
            if nickname:
                self.peer_client = PeerClient(self.server_ip, self.server_port, self.get_host_ip(), 33358, username=nickname, is_visitor=True)
                print(self.peer_client.register_visitor_with_tracker(nickname))
                nickname_window.destroy()  # Đóng cửa sổ nhập nickname
                self.root.destroy()
                self.open_main_app(nickname, is_visitor=True)
            else:
                messagebox.showwarning("Lỗi", "Nickname không được để trống!", parent=nickname_window)

        tk.Button(nickname_window, text="Confirm", command=confirm_nickname).pack(pady=10)
        nickname_entry.bind("<Return>", lambda event: confirm_nickname())

    def open_main_app(self, username, is_visitor):
        from peer3_main_app import Peer3MainApp
        main_window = tk.Tk()
        app = Peer3MainApp(main_window, username, self.peer_client, is_visitor)
        main_window.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = Peer3LoginApp(root)
    root.mainloop()