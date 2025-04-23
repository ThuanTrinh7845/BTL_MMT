# Network Application P2P Segment Chat
Network Application P2P Segment Chat là một ứng dụng mạng ngang hàng (P2P) cho phép người dùng đăng ký, đăng nhập, tạo kênh, tham gia kênh, trò chuyện qua tin nhắn và phát trực tuyến video/audio thời gian thực. Dự án được xây dựng để hỗ trợ giao tiếp phân đoạn ngang hàng, sử dụng lập trình socket cùng các thư viện như OpenCV, PyAudio, và Tkinter để xử lý đa phương tiện và giao diện người dùng.
## Cài đặt
Để chạy **Network Application P2P Segment Chat**, làm theo các bước sau:
- Sao chép kho lưu trữ:
  ```
  git clone https://github.com/ThuanTrinh7845/BTL_MMT.git
- Di chuyển vào thư mục dự án:
  ```
  cd BTL_MMT
- Cài đặt các phụ thuộc:
  ```
  pip install -r requirements.txt
## Sử dụng
- Khởi động tracker:
  ```
  python tracker1.py
  ```
  - Tracker quản lý người dùng, kênh và danh sách peer.
  - Mặc định chạy trên 192.168.227.241:22236. Chỉnh sửa địa chỉ IP và cổng trong tracker1.py nếu cần.
- Khởi động peer:
  ```bash
  python peer1_login.py (trong thư mục peer1)
  python peer2_login.py (trong thư mục peer2)
  python peer3_login.py (trong thư mục peer3)
  ```
  - Giao diện đăng nhập (peer1_login.py) cho phép đăng ký hoặc đăng nhập.
  - Sau khi đăng nhập, giao diện chính (peer1_main_app.py) mở ra để quản lý kênh và phát trực tuyến.
  - Mặc định peer chạy trên cổng 33357. Có thể thay đổi trong peer1_login.py.  
  
