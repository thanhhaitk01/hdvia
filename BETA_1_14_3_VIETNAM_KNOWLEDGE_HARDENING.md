# HDVIA Beta 1.14.3 — Vietnam Knowledge Hardening

## Mục tiêu
Khắc phục khoảng trống phát hiện ở Beta 1.14.2: Journey Engine nhận diện địa danh nhưng Conversation AI có thể thiếu tri thức để trả lời các câu hỏi lịch sử, văn hóa, ẩm thực và thuyết minh.

## Thay đổi
- Knowledge Layer fallback sang Destination Catalog và Vietnam Coverage Registry.
- Bổ sung hồ sơ curated cho Mỹ Sơn, Bản Giốc, Pác Bó, Đồng Văn, Cái Răng, Tháp Bà Ponagar, Hoa Lư và Cát Bà.
- Giữ nguyên nguyên tắc: recognized place không đồng nghĩa verified fact; dữ liệu thiếu vẫn phải được báo thiếu, không bịa.
- Cache resolve_known_place để giảm chi phí lặp lại trong stress tests.
- Version: `1.14.3-vietnam-knowledge-hardening`.

## Kiểm thử
- Journey/Conversation/Hardening targeted: 26/26 PASS.
- 1,000,000 deterministic core iterations: PASS (~26.5s trong môi trường kiểm thử).
- 1,000 full deterministic Journey analyses: PASS (~0.72s).

## Giới hạn còn lại
Đây chưa phải một cơ sở dữ liệu bách khoa toàn bộ Việt Nam. Registry có coverage rộng, nhưng độ sâu tri thức từng địa danh phụ thuộc dữ liệu curated. Bước tiếp theo nên là Knowledge Pack có nguồn, phiên bản và ngày cập nhật cho từng địa danh/di tích/làng nghề/bảo tàng.
