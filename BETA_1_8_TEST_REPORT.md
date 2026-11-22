# HDVIA BETA 1.8 — TEST REPORT

## Phiên bản
- Version: `1.8.1-beta-commercial`
- Slogan: **Trí tuệ đồng hành, hành trình chủ động.**
- Giao diện người dùng: tiếng Việt hoàn toàn.
- Logo HDVIA: đã tích hợp trong giao diện.
- Quyền Beta: người dùng đăng nhập bằng Google/Facebook/Zalo được dùng toàn bộ chức năng người dùng.
- Kho kinh nghiệm: người dùng đã đăng nhập có thể đăng bài và bài được đưa vào kho để thu thập dữ liệu thực tế.

## Kiểm thử tự động
- Pytest: **24 passed**.
- Python compileall: **PASS**.
- AST parse toàn bộ Python: **16/16 PASS**.
- Kiểm tra file/route/hợp đồng: **PASS**.
- Kiểm tra giao diện Việt hóa: **PASS**.
- Quét tên module kỹ thuật tiếng Anh trong template/static: **không phát hiện**.
- Kiểm tra 7 ngày thời tiết: **PASS**.
- Kiểm tra cảnh báo, lộ trình, thuyết minh, phương án dự phòng, điểm chất lượng: **PASS**.
- Kiểm tra quyền người dùng Beta: **PASS**.
- Kiểm tra Kho kinh nghiệm: **PASS**.

## Stress test
- **1.000.000 lượt** kiểm thử logic lõi deterministic: **PASS**.
- **1.000 lượt** phân tích hành trình đầy đủ với nhà cung cấp thời tiết giả lập: **PASS**.
- Thời gian chạy bài stress test: khoảng **5,98 giây** trong môi trường kiểm thử hiện tại.

## Phạm vi 1 triệu lượt
Các lượt stress tập trung vào các chức năng logic lõi có tính quyết định và có thể kiểm thử lặp lại: nhận diện điểm đến, phân tách ngày, chuẩn hóa 7 ngày thời tiết, phân loại rủi ro và tính khoảng cách. Các dịch vụ bên ngoài như Google/Facebook/Zalo, Open-Meteo và Wikimedia không được gọi 1 triệu lần vì đó là kiểm thử phụ thuộc mạng/nhà cung cấp và không phải cách kiểm thử an toàn hay có ý nghĩa.

## Giới hạn cần smoke-test sau deploy
Môi trường dựng gói hiện tại không có Flask/Authlib để chạy server Flask thực tế. Vì vậy chưa tuyên bố runtime production/Vercel đã được xác nhận. Sau khi deploy cần kiểm tra trực tiếp: trang chủ, đăng nhập Google/Facebook/Zalo, Phân tích hành trình, Thời tiết, Kho kinh nghiệm, đăng bài, hồ sơ và quản trị.
