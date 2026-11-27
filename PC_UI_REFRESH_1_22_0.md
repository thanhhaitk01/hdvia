# HDVIA Beta 1.22.0 — PC UI Refresh

## Phạm vi
- Chỉ chỉnh giao diện PC của module Hành Trình AI.
- Ẩn trên PC: `HDVIA HIỂU YÊU CẦU` và `CÂU HỎI GỢI Ý`.
- Người dùng nhập trực tiếp lịch trình, địa điểm hoặc câu hỏi tự do.
- Lịch trình nhiều ngày: thông tin điểm đến được trình bày theo từng ngày.
- Một địa điểm: hiển thị thông tin của địa điểm đó.
- Câu hỏi tự do: hiển thị câu trả lời trực tiếp.
- Giao diện Mobile giữ nguyên bằng cách giữ nguyên surface cũ trong `journey-mobile-legacy` và chỉ kích hoạt surface mới từ 901px trở lên.

## Kiểm thử
- Jinja template compile: PASS
- UI regression tests: PASS
- PC UI refresh tests: PASS
