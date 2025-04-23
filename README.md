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
  ```
  python peer1_login.py (trong thư mục peer1)
  python peer2_login.py (trong thư mục peer2)
  python peer3_login.py (trong thư mục peer3)
  ```
  - Giao diện đăng nhập (peer1_login.py) cho phép đăng ký hoặc đăng nhập.
  - Sau khi đăng nhập, giao diện chính (peer1_main_app.py) mở ra để quản lý kênh và phát trực tuyến.
  - Mặc định peer chạy trên cổng 33357. Có thể thay đổi trong peer1_login.py.
- Tạo và tham gia kênh:
  - Từ giao diện chính, nhấn "Tạo kênh mới" để tạo kênh hoặc nhập từ khóa vào ô tìm kiếm để tham gia kênh có sẵn.
  - Chỉ host (người tạo kênh) có thể phát trực tuyến.
- Phát trực tuyến:
  - Host nhấn "Bắt đầu Stream" để gửi video từ webcam và âm thanh từ microphone đến các peer trong kênh.
  - Các peer khác sẽ nhận và hiển thị stream trong giao diện.
## Tính năng  
- Quản lý người dùng: Đăng ký và đăng nhập thông qua tracker, lưu thông tin vào users.json.
- Quản lý kênh: Tạo kênh, tham gia kênh, tìm kiếm kênh bằng từ khóa.
- Trò chuyện phân đoạn: Gửi và nhận tin nhắn văn bản trong các kênh P2P.
- Phát trực tuyến P2P: Video (OpenCV) và audio (PyAudio) từ host đến các peer qua kết nối socket.
- Giao diện đồ họa: Sử dụng Tkinter để quản lý kênh, hiển thị tin nhắn và video.





