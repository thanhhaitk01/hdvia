# HDVIA Beta 1.10.11 — Hành trình AI Unified

## Chốt giao diện
- Gộp **Phân tích hành trình** và **Điểm đến & Thông tin** thành module duy nhất: **Hành trình AI**.
- Bỏ module điều hướng **Điểm đến & Thông tin** khỏi menu chính.
- Giữ URL `/destinations` để tương thích và tự chuyển về `/journey`.
- Một ô nhập nhận tên tỉnh/thành, điểm du lịch, địa danh hoặc cả lịch trình.

## Luồng dữ liệu
- AI intent resolver phân biệt yêu cầu điểm đến/địa danh và yêu cầu hành trình.
- Tra cứu kết hợp dữ liệu catalog, 34 tỉnh/thành, Kho tri thức và dữ liệu 8 kho khi đã có bản ghi ACTIVE/PUBLISHED.
- Ví dụ `Hà Nội` trả hồ sơ Hà Nội; `Lăng Khải Định` nhận diện thuộc Huế; chuỗi `Đà Nẵng → Hội An → Huế` nhận diện là hành trình.
- Đây là lớp **retrieval + intent**; chưa giả lập việc mô hình AI tự sinh dữ liệu chưa có trong kho.

## Kiểm thử
- 77/77 regression tests PASS.
- Python compile PASS.
- Đã loại bỏ `__pycache__`, `.pyc`, `.pytest_cache` và thư mục build lồng nhau trước khi đóng gói.
