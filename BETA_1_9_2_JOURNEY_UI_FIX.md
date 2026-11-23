# HDVIA Beta 1.9.2 — Journey UI Fix

## Sửa lỗi
- Chuyển 5 mục phân tích hành trình từ `span` không tương tác thành liên kết điều hướng theo từng khu vực.
- Thêm liên kết và vùng hiển thị riêng cho Tổng quan, Thời tiết, Cảnh báo, Lộ trình và Dự phòng.
- Thêm lộ trình theo từng ngày và khoảng cách chặng.
- Thêm phương án dự phòng theo từng ngày từ `plan_b`.
- Không render JSON thô của `weather`, `risk_map` hoặc `risks` trên giao diện.
- Giữ nguyên Google/Facebook Login, Unified Session và các nền tảng Connect của Beta 1.9.

## Kiểm tra
- Python compile: PASS
- Regression tests: PASS
