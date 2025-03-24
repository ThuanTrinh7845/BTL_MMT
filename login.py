import tkinter as tk
from tkinter import messagebox
from client import Client

class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Login")
        self.root.geometry("300x200")

        # API endpoint
        self.server_ip = "127.0.0.1"  # Địa chỉ IP của server
        self.server_port = 22236  # Cổng của server

        # Khởi tạo client
        self.client = Client(self.server_ip, self.server_port)

        # Tạo các thành phần UI
        self.create_login_ui()

    def create_login_ui(self):
        # Label và Entry cho Username
        tk.Label(self.root, text="Username:").pack(pady=5)
        self.username_entry = tk.Entry(self.root)
        self.username_entry.pack(pady=5)

        # Label và Entry cho Password
        tk.Label(self.root, text="Password:").pack(pady=5)
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.pack(pady=5)

        # Nút Login
        tk.Button(self.root, text="Login", command=self.attempt_login).pack(pady=10)

        # Nút Register
        tk.Button(self.root, text="Register", command=self.attempt_register).pack(pady=10)

    def attempt_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        # Gọi server để đăng nhập
        response = self.client.call_server("login", username, password)

        if response == "Login successful":
            messagebox.showinfo("Login Success", "Đăng nhập thành công!")
            self.root.destroy()  # Đóng cửa sổ đăng nhập
            self.open_main_app(username)  # Mở màn hình chính
        else:
            messagebox.showerror("Login Failed", "Tên đăng nhập hoặc mật khẩu không đúng!")

    def attempt_register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        # Gọi server để đăng ký
        response = self.client.call_server("register", username, password)

        if response == "Register successful":
            messagebox.showinfo("Register Success", "Đăng ký thành công!")
        else:
            messagebox.showerror("Register Failed", "Đăng ký thất bại!")

    def open_main_app(self, username):
        from main_app import MainApp
        main_window = tk.Tk()
        app = MainApp(main_window, username)
        main_window.mainloop()