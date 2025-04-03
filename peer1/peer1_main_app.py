import tkinter as tk
import queue
from tkinter import messagebox, scrolledtext
import tkinter.simpledialog

class Peer1MainApp:
    def __init__(self, root, username, peer_client):
        self.root = root
        self.root.title("Peer1 - P2P Segment Chat")
        self.root.geometry("700x700")
        self.username = username
        self.peer_client = peer_client

        # Nhãn trạng thái
        self.status_label = tk.Label(self.root, text="Trạng thái: ONLINE", fg="green", font=("Arial", 10, "bold"))
        self.status_label.place(x=10, y=10)

        # Hiển thị thông tin người dùng
        tk.Label(self.root, text=f"Xin chào, {username}!", font=("Arial", 16)).pack(pady=10)

        # Tạo frame để chứa nút, thanh tìm kiếm và danh sách kênh
        self.channel_frame = tk.Frame(self.root)
        self.channel_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # Nút tạo kênh mới (nằm trên cùng trong frame)
        self.create_channel_button = tk.Button(self.channel_frame, text="Tạo kênh mới", command=self.create_new_channel)
        self.create_channel_button.pack(side=tk.TOP, padx=10, pady=(0, 5))  # Khoảng cách nhỏ phía dưới nút

        # Thanh tìm kiếm kênh (nằm giữa)
        self.search_label = tk.Label(self.channel_frame, text="Tìm kiếm kênh:")
        self.search_label.pack(side=tk.TOP, anchor='w', padx=10)
        self.search_entry = tk.Entry(self.channel_frame)
        self.search_entry.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(0, 5))
        self.search_entry.bind("<KeyRelease>", self.filter_channels)

        # Danh sách kênh (nằm ngay dưới nút trong frame)
        self.channel_listbox = tk.Listbox(self.channel_frame)
        self.channel_listbox.pack(side=tk.TOP, fill=tk.Y, expand=True)  # Chiếm không gian còn lại
        self.channel_listbox.bind("<<ListboxSelect>>", self.on_channel_select)  

        # Đồng bộ danh sách kênh từ peer_client
        self.sync_channel_list()

        # Cửa sổ hiển thị tin nhắn
        self.message_display = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state='disabled')
        self.message_display.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Frame chứa ô nhập tin nhắn và các nút
        self.message_frame = tk.Frame(self.root)
        self.message_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        # Ô nhập tin nhắn
        self.message_entry = tk.Entry(self.message_frame)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Nút gửi tin nhắn
        self.send_button = tk.Button(self.message_frame, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT)
        
        # Nút tham gia kênh (ẩn ban đầu)
        self.join_button = tk.Button(self.message_frame, text="Tham gia kênh", command=self.join_channel)
        self.join_button.pack(side=tk.RIGHT)
        self.join_button.pack_forget()

    def create_new_channel(self):
        """Hàm xử lý việc tạo kênh mới"""
        channel_id = tk.simpledialog.askstring("Tạo kênh mới", "Nhập tên kênh:")
        if channel_id:
            if self.peer_client.create_channel(channel_id):
                self.sync_channel_list()
                messagebox.showinfo("Thành công", f"Kênh {channel_id} đã được tạo.")
            else:
                # Nếu tạo kênh thất bại, hiển thị thông báo lỗi
                messagebox.showerror("Lỗi", f"Không thể tạo kênh {channel_id}.")

    def filter_channels(self, event):
        """Lọc danh sách kênh theo từ khóa nhập từ Tracker"""
        keyword = self.search_entry.get().lower()
        # self.channel_listbox.delete(0, tk.END)
        if keyword:
            channels = self.peer_client.search_channels(keyword)
            self.channel_listbox.delete(0, tk.END)
            for channel in channels:
                self.channel_listbox.insert(tk.END, f"{channel}")
        else:
            self.sync_channel_list()

    def sync_channel_list(self):
        self.channel_listbox.delete(0, tk.END)
        for channel_id in self.peer_client.hosted_channels.keys():
            self.channel_listbox.insert(tk.END, channel_id)
        for channel_id in self.peer_client.joined_channels.keys():
            self.channel_listbox.insert(tk.END, channel_id)

    def on_channel_select(self, event):
        """Xử lý khi chọn một kênh từ danh sách"""
        selected = self.channel_listbox.curselection()
        if selected:
            channel_id = self.channel_listbox.get(selected[0]).split()[0]  # Lấy channel_id
            if channel_id in self.peer_client.joined_channels or channel_id in self.peer_client.hosted_channels:
                # Kênh đã tham gia hoặc đang host
                self.display_channel_history(channel_id)
                self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                self.send_button.pack(side=tk.RIGHT)
                self.join_button.pack_forget()  # Ẩn nút tham gia
            else:
                # Kênh chưa tham gia
                self.message_entry.pack_forget()
                self.send_button.pack_forget()
                self.join_button.pack(side=tk.RIGHT)
                self.message_display.config(state='normal')
                self.message_display.delete(1.0, tk.END)
                self.message_display.insert(tk.END, f"Kênh {channel_id} chưa tham gia.\n")
                self.message_display.config(state='disabled')
    
    def join_channel(self):
        """Tham gia kênh được chọn"""
        selected = self.channel_listbox.curselection()
        if selected:
            channel_id = self.channel_listbox.get(selected[0]).split()[0]
            if self.peer_client.join_channel(channel_id):
                messagebox.showinfo("Thành công", f"Đã tham gia kênh {channel_id}.")
                self.sync_channel_list()
                self.on_channel_select(None)  # Cập nhật giao diện
            else:
                messagebox.showerror("Lỗi", f"Không thể tham gia kênh {channel_id}.")

    def display_channel_history(self, channel_id):
        if channel_id in self.peer_client.hosted_channels:
            history = self.peer_client.hosted_channels[channel_id]
            self.message_display.config(state='normal')
            self.message_display.delete(1.0, tk.END)
            for timestamp, author, content in history:
                self.message_display.insert(tk.END, f"{author}: {content}\n")
            self.message_display.config(state='disabled')
        elif channel_id in self.peer_client.joined_channels:
            history = self.peer_client.joined_channels[channel_id]
            self.message_display.config(state='normal')
            self.message_display.delete(1.0, tk.END)
            for timestamp, author, content in history:
                self.message_display.insert(tk.END, f"{author}: {content}\n")
            self.message_display.config(state='disabled')

    def send_message(self):
        selected_channel = self.channel_listbox.get(self.channel_listbox.curselection())
        message = self.message_entry.get()
        if selected_channel and message:
            self.peer_client.send_message(selected_channel, message)
            self.message_entry.delete(0, tk.END)
            self.check_queue()
            
    def check_queue(self):
        try:
            while True:
                # Lấy tin nhắn từ queue mà không chặn
                channel_id, username, message = self.peer_client.message_queue.get_nowait()
                self.update_message_display(channel_id, username, message)
        except queue.Empty:
            pass
        # Lên lịch kiểm tra lại sau 100ms
        self.root.after(100, self.check_queue)

    def update_message_display(self, channel_id, username, message):
        # Lấy kênh hiện tại đang chọn
        selected_channel = self.channel_listbox.get(self.channel_listbox.curselection())
        if selected_channel == channel_id:
            self.message_display.config(state='normal')
            self.message_display.insert(tk.END, f"{username}: {message}\n")
            self.message_display.config(state='disabled')
            self.message_display.see(tk.END)  # Cuộn xuống tin nhắn mới nhất

    def update_status(self, status):
        self.status_label.config(text=f"Trạng thái: {status}")