# HDVIA Beta 1.12.0 — Conversation Intelligence

## Mục tiêu
Nâng Hành Trình AI từ mô hình nhập câu hỏi → phân tích sang lớp giao tiếp chủ động:
- Nhận diện intent đa chủ đề.
- Nhận diện địa điểm trên toàn bộ dữ liệu tỉnh/thành 2025 và catalog điểm đến.
- Dự đoán câu hỏi tiếp theo.
- Trả lời theo dữ liệu kiểm duyệt/catalog; không tự bịa khi thiếu nguồn.
- Hiển thị độ tin cậy và nguồn tham chiếu.
- Giữ Journey Intelligence cho thời tiết, rủi ro, route và itinerary.

## Thành phần mới
- `conversation_engine.py`
- `ConversationIntelligenceEngine`
- UI CÂU HỎI GỢI Ý trong `templates/journey.html`.
- Trợ lý `/tro-ly-ai` dùng cùng Conversation Intelligence thay vì bộ từ khóa cũ.

## Luồng
`User Query → Intent + Place Understanding → Conversation Intelligence → Data/Knowledge/Journey Context → Answer + Predicted Questions`

## Kiểm thử
- 82/82 tests PASS.
- Đã kiểm tra các luồng mẫu: thời tiết, địa điểm tỉnh/thành, điểm tham quan, khách quốc tế + mưa + thuyết minh/Plan B, câu hỏi không có dữ liệu.
- Không đóng gói `.pyc`, `.pyo`, `__pycache__`, `.pytest_cache`.

## Giới hạn đã xác nhận
Bản này vẫn là lớp Conversation Intelligence provider-neutral. Chưa tích hợp LLM bên ngoài để sinh văn bản tự do; câu trả lời hiện được tổng hợp có kiểm soát từ dữ liệu HDVIA. Đây là chủ ý an toàn cho Beta và phù hợp pipeline kiểm duyệt dữ liệu.
