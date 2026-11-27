# HDVIA Beta 1.25.2.5 — Verified Image Entity Resolution

## Mục tiêu
Sửa lỗi ảnh đại diện có thể lấy nhầm ảnh của địa điểm khác dù Wikimedia API trả HTTP 200.

## Thay đổi
- Thêm `image_entity_resolution.py`.
- Khóa ảnh theo entity trước khi chọn ảnh.
- Ưu tiên Wikidata `P18` của entity đã resolve.
- Đối chiếu tên/alias đa ngôn ngữ, tiêu đề, mô tả, category.
- Đối chiếu tọa độ ảnh khi Wikimedia cung cấp GPS metadata.
- Bổ sung Commons geosearch làm tín hiệu phụ.
- Chấm điểm mức độ phù hợp và confidence.
- Ngưỡng xác minh: ảnh không đạt ngưỡng sẽ không được hiển thị.
- Nếu không có bằng chứng đủ mạnh, HDVIA fail-closed thay vì lấy ảnh ngẫu nhiên.
- Endpoint `/api/v1/place-image` trả cả `entity_resolution`, `entity_id`, `score`, `confidence`, `evidence`.
- Không thay đổi giao diện hoặc thêm module.
- Giữ nguyên canonical name của Journey AI.

## QA
- `python -m compileall -q .` — PASS.
- Unit regression mới: 3/3 PASS cho Verified Image Resolution.
- Regression API connectivity: PASS.
- Tổng test suite tại thời điểm đóng bản: 8/8 PASS.

## Tiêu chuẩn mới
`HTTP 200` chỉ chứng minh provider sống; không còn được xem là bằng chứng ảnh đúng.
Ảnh đại diện chỉ được render khi entity match đủ mạnh.

## Test chuẩn
`Chùa Cầu Hội An -> Japanese Bridge -> Q1091054 -> Wikimedia P18 -> ảnh xác minh`.
