import tkinter as tk
from tkinter import scrolledtext

class MainApp:
    def __init__(self, root, username):
        self.root = root
        self.root.title("P2P Segment Chat")
        self.root.geometry("700x700")
        # Nhãn hiển thị trạng thái hoạt động
        self.status_label = tk.Label(self.root, text="Trạng thái: Đang kết nối...", fg="green", font=("Arial", 10, "bold"))
        self.status_label.place(x=10, y=10)  # Đặt ở góc trái phía trên

        # Hiển thị thông tin người dùng đã đăng nhập
        tk.Label(self.root, text=f"Xin chào, {username}!", font=("Arial", 16)).pack(pady=10)

        # Danh sách kênh
        self.channel_listbox = tk.Listbox(self.root)
        self.channel_listbox.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # Thêm các kênh mẫu
        self.channel_listbox.insert(tk.END, "Channel 1")
        self.channel_listbox.insert(tk.END, "Channel 2")
        self.channel_listbox.insert(tk.END, "Channel 3")

        # Cửa sổ hiển thị tin nhắn
        self.message_display = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state='disable')
        self.message_display.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Hộp nhập tin nhắn
        self.message_entry = tk.Entry(self.root)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)
        # Nút gửi tin nhắn
        self.send_button = tk.Button(self.root, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT, padx=10, pady=10)
    # Hiển thị trạng thái
    def update_status(self, status):
        self.status_label.config(text=f"Trạng thái: {status}")

    def send_message(self):
        message = self.message_entry.get()
        if message:
            # Hiển thị tin nhắn trong cửa sổ chat
            self.message_display.config(state='normal')
            self.message_display.insert(tk.END, f"You: {message}\n")
            self.message_display.config(state='disable')
            self.message_entry.delete(0, tk.END)