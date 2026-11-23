# HDVIA Beta 1.8.5 – UI Refresh

Baseline: **HDVIA Beta 1.8.4 GitHub Ready**.

## Changes
- Giữ nguyên kiến trúc và chức năng của 1.8.4 làm nền.
- Tiếp tục Việt hóa giao diện theo bố cục đã chốt; dùng nhãn **Trợ lý hành trình** thay cho tên giao diện cũ.
- Làm mới hero trang chủ theo hướng trung tâm điều hành hành trình, giảm chữ thừa và tăng khả năng thao tác.
- Thêm lớp giao diện `location-aware`: trình duyệt có thể cung cấp vị trí hiện tại, hệ thống xác định điểm đến gần nhất từ catalog và cập nhật nhãn giao diện.
- Thêm nền minh họa du lịch nội bộ để không phụ thuộc CDN/hình ảnh bên thứ ba.
- Thêm endpoint `/api/v1/location-context` và test contract cho cơ chế vị trí.
- Giữ nguyên cơ chế tài khoản quản trị và phân quyền hiện có.

## Validation
- `pytest -q`
- Kết quả: **30 passed**.

## Deploy
Upload toàn bộ nội dung ZIP lên GitHub theo cấu trúc thư mục hiện tại, sau đó commit/deploy như quy trình 1.8.4.

## UI Simplification
- Ẩn các lối truy cập riêng cho Thời tiết & Cảnh báo và Trợ lý hành trình khỏi thanh điều hướng chính.
- Gộp Thời tiết, Cảnh báo, Lộ trình và phương án dự phòng vào luồng Lập & phân tích hành trình.
- Gộp Điểm đến và thông tin điểm đến thành một khu vực.
- Gộp Kho kinh nghiệm và Cộng đồng HDV thành một khu vực.
- Giảm các thẻ chức năng trang chủ từ 6 xuống 4 nhóm chính.
- Giữ các route backend cũ để tránh phá vỡ chức năng, chỉ tinh gọn điểm truy cập trên giao diện.

Validation after simplification: **31 passed**.
