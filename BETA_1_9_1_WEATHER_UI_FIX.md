# HDVIA Beta 1.9.1 — Weather UI Fix

## Mục tiêu
Sửa lỗi hiển thị dữ liệu thời tiết trên trang **Lập & phân tích hành trình**.

## Đã sửa
- Không còn render JSON/raw weather data trực tiếp lên giao diện.
- Hiển thị dự báo 7 ngày theo từng điểm đến dưới dạng thẻ trực quan.
- Hiển thị nhiệt độ cao/thấp, trạng thái thời tiết, xác suất mưa và tốc độ gió.
- Chuyển mã thời tiết thành biểu tượng và tên trạng thái dễ đọc.
- Chuyển cảnh báo rủi ro từ dữ liệu kỹ thuật sang giao diện theo mức độ: Cao / Trung bình / Thấp.
- Giữ nguyên API và cấu trúc dữ liệu Journey Intelligence hiện tại.
- Giữ nguyên các chức năng đăng nhập, Unified Session, Google/Facebook và các module Beta 1.9.

## Regression test
`43 passed`

## GitHub
Giải nén ZIP và đưa toàn bộ nội dung vào **root repository**. Không upload ZIP lồng trong repository.
