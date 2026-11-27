# HDVIA Beta 1.25.2.4 — Entity Resolution + Knowledge Fusion

## Mục tiêu
Khắc phục điểm nghẽn đã xác nhận trong QA: Wikidata hoạt động nhưng truy vấn tiếng Việt `Chùa Cầu Hội An` không tự liên kết tới thực thể tiếng Anh `Japanese Bridge` (Q1091054).

## Thay đổi
- Thêm `entity_resolution.py` làm lớp cầu nối giữa tên địa điểm, Wikipedia và Wikidata.
- Chuẩn hóa tiếng Việt không dấu và hỗ trợ alias đa ngôn ngữ cho các địa danh/điểm nổi bật có tần suất cao.
- Ưu tiên: tên gốc -> alias đa ngôn ngữ -> tiêu đề Wikipedia tiếng Anh -> tìm Wikidata.
- Giữ nguyên tên địa điểm canonical trong Journey AI.
- Knowledge Fusion bổ sung `entity_resolution` và `wikidata.resolved`, không thay thế dữ liệu thô của provider.
- Bổ sung `id`, `label`, `match` vào phần tóm tắt kết quả provider để không làm mất mã thực thể Wikidata.
- Không thay đổi giao diện hoặc thêm module.

## QA
- `python -m compileall -q .` — PASS
- 16 regression tests liên quan — PASS
- Regression mới: `Chùa Cầu Hội An` -> `Japanese Bridge` -> `Q1091054` — PASS

## Giới hạn
Bản này chưa tuyên bố mọi địa danh Việt Nam đều được resolve tự động. Alias được giới hạn ở các trường hợp có độ tin cậy cao; các trường hợp mơ hồ vẫn phải được xác nhận trước khi dùng cho routing/knowledge fusion.
