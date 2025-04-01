import tkinter as tk
from tkinter import scrolledtext

class MainApp:
    def __init__(self, root, username):
        self.root = root
        self.root.title("P2P Segment Chat")
        self.root.geometry("700x700")
        self.username = username
        
        # Khởi tạo dữ liệu tin nhắn theo kênh
        self.channels = {
            "Channel 1": [],
            "Channel 2": [],
            "Channel 3": []
        }
        self.current_channel = None  # Kênh đang được chọn

        # UI Components
        self.setup_ui()

    def setup_ui(self):
        # Nhãn trạng thái
        self.status_label = tk.Label(self.root, text="Trạng thái: Đang kết nối...", fg="green", font=("Arial", 10, "bold"))
        self.status_label.place(x=10, y=10)

        # Hiển thị người dùng
        tk.Label(self.root, text=f"Xin chào, {self.username}!", font=("Arial", 16)).pack(pady=10)

        # Danh sách kênh
        self.channel_listbox = tk.Listbox(self.root)
        for channel in self.channels.keys():
            self.channel_listbox.insert(tk.END, channel)
        self.channel_listbox.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        self.channel_listbox.bind("<<ListboxSelect>>", self.on_channel_select)  # Thêm sự kiện chọn kênh

        # Cửa sổ tin nhắn
        self.message_display = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state='disabled')
        self.message_display.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Hộp nhập tin nhắn và nút gửi
        self.message_entry = tk.Entry(self.root)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)
        self.send_button = tk.Button(self.root, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT, padx=10, pady=10)

    def on_channel_select(self, event):
        """Xử lý khi chọn kênh"""
        selected_index = self.channel_listbox.curselection()
        if selected_index:
            channel_name = self.channel_listbox.get(selected_index[0])
            self.current_channel = channel_name
            self.update_message_display()

    def update_message_display(self):
        """Cập nhật cửa sổ tin nhắn theo kênh"""
        self.message_display.config(state='normal')
        self.message_display.delete(1.0, tk.END)
        for msg in self.channels[self.current_channel]:
            self.message_display.insert(tk.END, msg + "\n")
        self.message_display.config(state='disabled')

    def send_message(self):
        """Gửi tin nhắn vào kênh hiện tại"""
        if not self.current_channel:
            return
            
        message = self.message_entry.get()
        if message:
            full_msg = f"{self.username}: {message}"
            # Lưu tin nhắn vào kênh hiện tại
            self.channels[self.current_channel].append(full_msg)
            # Cập nhật giao diện
            self.update_message_display()
            self.message_entry.delete(0, tk.END)

    def update_status(self, status):
        self.status_label.config(text=f"Trạng thái: {status}")