# HDVIA Beta 1.8

## Chốt sản phẩm
- Logo HDVIA mới và slogan: **Bạn Đồng Hành Du Lịch Việt Nam**
- Giao diện người dùng Việt hóa hoàn toàn.
- Tên chức năng dùng ngôn ngữ dễ hiểu: Phân tích hành trình, Thời tiết hành trình, Cảnh báo rủi ro, Lộ trình & khoảng cách, Trợ lý thuyết minh, Phương án dự phòng, Thông tin điểm đến, Trợ lý AI.
- Beta mở đầy đủ chức năng cho người dùng đã đăng nhập bằng Google, Facebook hoặc Zalo.
- Bổ sung **Kho kinh nghiệm**: người dùng đã đăng nhập được viết và đăng bài chia sẻ kinh nghiệm.
- Xác minh HDV vẫn xét duyệt thủ công; chưa bật tự động xác minh thẻ.

## Kiểm thử
- Kiểm thử cấu trúc, biên dịch và hợp đồng API.
- 1.000.000 lượt kiểm thử logic lõi deterministic.
- 1.000 lượt phân tích hành trình đầy đủ với nhà cung cấp thời tiết giả lập.
- Kiểm tra 7 ngày thời tiết, cảnh báo, lộ trình, thuyết minh, phương án dự phòng, chất lượng, quyền truy cập và Kho kinh nghiệm.
- Kiểm thử runtime Flask thực tế phụ thuộc môi trường có Flask/Authlib và cấu hình OAuth của từng nhà cung cấp; phải smoke-test sau deploy.
