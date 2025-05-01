import tkinter as tk
import queue
from tkinter import messagebox, scrolledtext
import tkinter.simpledialog
from PIL import Image, ImageTk
import cv2
from peer2_login import Peer2LoginApp

class Peer2MainApp:
    def __init__(self, root, username, peer_client, is_visitor=False):
        self.root = root
        self.root.title("Peer2 - P2P Segment Chat")
        self.root.geometry("700x700")
        self.is_visitor = is_visitor
        self.username = username
        self.peer_client = peer_client
        self.current_channel = None  # Biến để theo dõi channel đang chọn
        self.viewing_streams = {}  # Dictionary để theo dõi trạng thái xem stream của từng kênh
        self.is_streaming = False  # Biến để kiểm soát việc peer có đang livestream hay không

        self.status_label = tk.Label(self.root, text="Trạng thái: ONLINE", fg="green", font=("Arial", 10, "bold"))
        self.status_label.place(x=10, y=10)

        tk.Label(self.root, text=f"Xin chào, {username}!", font=("Arial", 16)).pack(pady=10)

        self.channel_frame = tk.Frame(self.root)
        self.channel_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        self.search_label = tk.Label(self.channel_frame, text="Tìm kiếm kênh:")
        self.search_label.pack(side=tk.TOP, anchor='w', padx=10)
        self.search_entry = tk.Entry(self.channel_frame)
        self.search_entry.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(0, 5))
        self.search_entry.bind("<KeyRelease>", self.filter_channels)

        self.channel_listbox = tk.Listbox(self.channel_frame)
        self.channel_listbox.pack(side=tk.TOP, fill=tk.Y, expand=True)
        self.channel_listbox.bind("<<ListboxSelect>>", self.on_channel_select)

        self.message_display = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state='disabled')
        self.message_display.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.video_label = tk.Label(self.root)
        self.video_label.pack(side=tk.TOP, padx=10, pady=10)
        self.video_label.pack_forget()  # Ẩn video label mặc định

        self.message_frame = tk.Frame(self.root)
        self.message_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        self.view_stream_button = tk.Button(self.message_frame, text="Xem Stream", command=self.toggle_view_stream)
        self.view_stream_button.pack(side=tk.RIGHT)
        self.view_stream_button.pack_forget()  # Ẩn mặc định

        if not self.is_visitor:
            self.create_channel_button = tk.Button(self.channel_frame, text="Tạo kênh mới", command=self.create_new_channel)
            self.create_channel_button.pack(side=tk.TOP, padx=10, pady=(0, 5))

            self.sync_channel_list()

            self.message_entry = tk.Entry(self.message_frame)
            self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

            self.send_button = tk.Button(self.message_frame, text="Send", command=self.send_message)
            self.send_button.pack(side=tk.RIGHT)

            self.join_button = tk.Button(self.message_frame, text="Tham gia kênh", command=self.join_channel)
            self.join_button.pack(side=tk.RIGHT)
            self.join_button.pack_forget()

            self.stream_button = tk.Button(self.message_frame, text="Bắt đầu Stream", command=self.toggle_stream)
            self.stream_button.pack(side=tk.RIGHT)
            self.stream_button.pack_forget()

            self.logout_button = tk.Button(self.root, text="Log out", command=self.logout)
            self.logout_button.place(x=600, y=10)

            self.privacy_frame = tk.Frame(self.root)
            self.privacy_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(0, 5))

            self.privacy_button = tk.Button(self.privacy_frame, text="Make Private", command=self.toggle_channel_privacy)
            self.privacy_button.pack(side=tk.LEFT)
            self.privacy_button.pack_forget()
        else:
            self.logout_button = tk.Button(self.root, text="Log in", command=self.login)
            self.logout_button.place(x=600, y=10)

        self.check_queue()
        self.update_video()

        self.streaming_channel = None  # Channel đang stream
        self.current_channel = None   # Channel đang chọn

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def login(self):
        """Xử lý sự kiện khi nhấn nút Log out"""
        if messagebox.askokcancel("Đăng nhập", "Bạn muốn đăng nhập?"):
            if self.peer_client.streaming:
                self.peer_client.stop_stream()
            if self.peer_client.server_socket:
                self.peer_client.server_socket.close()
            self.root.destroy()
            self.open_login_window()

    def logout(self):
        """Xử lý sự kiện khi nhấn nút Log out"""
        if messagebox.askokcancel("Đăng xuất", "Bạn có chắc muốn đăng xuất?"):
            if self.peer_client.streaming:
                self.peer_client.stop_stream()
            if self.peer_client.server_socket:
                self.peer_client.server_socket.close()
            self.root.destroy()
            self.open_login_window()

    def open_login_window(self):
        """Mở lại giao diện đăng nhập từ peer1_login.py"""
        login_root = tk.Tk()
        login_app = Peer2LoginApp(login_root)
        login_root.mainloop()

    def create_new_channel(self):
        channel_id = tk.simpledialog.askstring("Tạo kênh mới", "Nhập tên kênh:")
        if channel_id and self.peer_client.create_channel(channel_id):
            self.sync_channel_list()
            messagebox.showinfo("Thành công", f"Kênh {channel_id} đã được tạo.")

    def filter_channels(self, event):
        keyword = self.search_entry.get().lower()
        if keyword:
            channels = self.peer_client.search_channels(keyword)
            self.channel_listbox.delete(0, tk.END)
            for channel in channels:
                self.channel_listbox.insert(tk.END, f"{channel}")
        else:
            if not self.is_visitor:
                self.sync_channel_list()

    def sync_channel_list(self):
        self.channel_listbox.delete(0, tk.END)
        for channel_id in self.peer_client.hosted_channels.keys():
            self.channel_listbox.insert(tk.END, channel_id)
        for channel_id in self.peer_client.joined_channels.keys():
            self.channel_listbox.insert(tk.END, channel_id)

    def toggle_channel_privacy(self):
        """Thay đổi trạng thái private/public của kênh"""
        if self.current_channel and self.current_channel in self.peer_client.hosted_channels:
            current_privacy = self.peer_client.get_channel_privacy(self.current_channel)
            new_privacy = "private" if current_privacy == "public" else "public"
            success = self.peer_client.set_channel_privacy(self.current_channel, new_privacy)
            if success:
                self.privacy_button.config(text=f"Make {'Private' if new_privacy == 'public' else 'Public'}")
                messagebox.showinfo("Thành công", f"Kênh {self.current_channel} đã được đặt thành {new_privacy}!")
            else:
                messagebox.showerror("Lỗi", "Không thể thay đổi trạng thái kênh!")
        else:
            messagebox.showwarning("Lỗi", "Bạn không phải host của kênh này!")

    def on_channel_select(self, event):
        selected = self.channel_listbox.curselection()
        if selected:
            channel_id = self.channel_listbox.get(selected[0]).split()[0]
            self.current_channel = channel_id  # Cập nhật channel đang chọn
            if self.viewing_streams.get(channel_id, False) or (self.is_streaming and self.streaming_channel == channel_id):
                self.video_label.pack(side=tk.TOP, padx=10, pady=10)
                self.view_stream_button.config(text="Dừng Xem")
            else:
                self.video_label.pack_forget()
                self.view_stream_button.config(text="Xem Stream")

            if self.is_visitor:
                if not self.peer_client.can_visitor_view(channel_id):
                    self.message_display.config(state='normal')
                    self.message_display.delete(1.0, tk.END)
                    self.message_display.insert(tk.END, f"Kênh {channel_id} không cho phép visitor xem.\n")
                    self.message_display.config(state='disabled')
                    self.video_label.pack_forget()
                    return
                else:
                    self.display_channel_history(channel_id)
            elif channel_id in self.peer_client.joined_channels or channel_id in self.peer_client.hosted_channels:
                self.display_channel_history(channel_id)
                self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                self.send_button.pack(side=tk.RIGHT)
                self.join_button.pack_forget()
                self.stream_button.pack(side=tk.RIGHT)
                self.view_stream_button.pack(side=tk.RIGHT)
                if channel_id in self.peer_client.hosted_channels:
                    # Hiển thị nút Toggle Privacy và cập nhật trạng thái
                    current_privacy = self.peer_client.get_channel_privacy(channel_id)
                    self.privacy_button.config(text=f"Make {'Private' if current_privacy == 'public' else 'Public'}")
                    self.privacy_button.pack(side=tk.RIGHT)
                else:
                    self.privacy_button.pack_forget()
            else:
                self.message_entry.pack_forget()
                self.send_button.pack_forget()
                self.join_button.pack(side=tk.RIGHT)
                self.stream_button.pack_forget()
                self.video_label.pack_forget()
                self.privacy_button.pack_forget()
                if not self.peer_client.can_visitor_view(channel_id):
                    self.message_display.config(state='normal')
                    self.message_display.delete(1.0, tk.END)
                    self.message_display.insert(tk.END, f"Kênh {channel_id} riêng tư.\n")
                    self.message_display.config(state='disabled')
                else:
                    self.display_channel_history(channel_id)
                    self.view_stream_button.pack(side=tk.RIGHT)

    def join_channel(self):
        selected = self.channel_listbox.curselection()
        if selected:
            channel_id = self.channel_listbox.get(selected[0]).split()[0]
            if self.peer_client.join_channel(channel_id):
                messagebox.showinfo("Thành công", f"Đã tham gia kênh {channel_id}.")
                self.sync_channel_list()
                self.on_channel_select(None)

    def display_channel_history(self, channel_id):
        if self.is_visitor:
            history = self.peer_client.get_content_channel_id(channel_id)
        elif channel_id in self.peer_client.hosted_channels:
            history = self.peer_client.hosted_channels[channel_id]
        elif channel_id in self.peer_client.joined_channels:
            history = self.peer_client.joined_channels[channel_id]
        else:
            history = self.peer_client.get_content_channel_id(channel_id)
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
                channel_id, username, message = self.peer_client.message_queue.get_nowait()
                self.update_message_display(channel_id, username, message)
        except queue.Empty:
            pass
        self.root.after(100, self.check_queue)

    def update_message_display(self, channel_id, username, message):
        selected_channel = self.channel_listbox.get(self.channel_listbox.curselection())
        if selected_channel == channel_id:
            self.message_display.config(state='normal')
            self.message_display.insert(tk.END, f"{username}: {message}\n")
            self.message_display.config(state='disabled')
            self.message_display.see(tk.END)

    def toggle_stream(self):
        selected_channel = self.channel_listbox.get(self.channel_listbox.curselection())
        if selected_channel: #and selected_channel in self.peer_client.hosted_channels:
            if self.stream_button["text"] == "Bắt đầu Stream":
                self.peer_client.start_stream(selected_channel)
                self.stream_button.config(text="Dừng Stream")
                self.streaming_channel = selected_channel
                self.is_streaming = True
                # self.current_channel = selected_channel  # Đảm bảo channel hiện tại khớp
                if self.current_channel == selected_channel:
                    self.video_label.pack(side=tk.TOP, padx=10, pady=10)
                print(f"Bắt đầu stream trên {selected_channel}")
            else:
                self.peer_client.stop_stream(selected_channel)
                self.stream_button.config(text="Bắt đầu Stream")
                self.streaming_channel = None
                self.is_streaming = False
                if not self.viewing_streams.get(self.current_channel, False):
                    self.video_label.pack_forget()
                print("Dừng stream")

    def toggle_view_stream(self):
        if self.current_channel:
            # Chuyển đổi trạng thái xem stream cho kênh hiện tại
            self.viewing_streams[self.current_channel] = not self.viewing_streams.get(self.current_channel, False)
            if self.viewing_streams[self.current_channel]:
                self.view_stream_button.config(text="Dừng Xem")
                self.video_label.pack(side=tk.TOP, padx=10, pady=10)  # Hiển thị widget video
                print(f"Đang xem stream trên {self.current_channel}")
            else:
                self.view_stream_button.config(text="Xem Stream")
                # Chỉ ẩn widget nếu không còn livestream ở kênh hiện tại
                if not (self.is_streaming and self.streaming_channel == self.current_channel):
                    self.video_label.pack_forget()
                print(f"Dừng xem stream trên {self.current_channel}")

    def update_video(self):
        if self.current_channel:
            if self.viewing_streams.get(self.current_channel, False) or (self.is_streaming and self.streaming_channel == self.current_channel):
                queues = self.peer_client.video_queues.get(self.current_channel)
                if queues:
                    try:
                        frame = queues.get_nowait()
                        if frame is None:
                            self.video_label.pack_forget()
                        else:
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            frame = cv2.resize(frame, (320, 240))
                            img = Image.fromarray(frame)
                            imgtk = ImageTk.PhotoImage(image=img)
                            self.video_label.imgtk = imgtk
                            self.video_label.configure(image=imgtk)
                            if not self.video_label.winfo_ismapped():
                                self.video_label.pack(side=tk.TOP, padx=10, pady=10)
                    except queue.Empty:
                        pass
                else:
                    self.video_label.pack_forget()
        else:
            self.video_label.pack_forget()
        self.root.after(10, self.update_video)

    def on_closing(self):
        if messagebox.askokcancel("Thoát", "Bạn có chắc muốn thoát chương trình?"):
            if self.peer_client.streaming:
                self.peer_client.stop_stream()
            if self.peer_client.server_socket:
                self.peer_client.server_socket.close()
            self.root.destroy()
            exit(0)