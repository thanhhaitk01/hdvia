# HDVIA BETA 1.23 — AI CONNECT & SELF-UPDATE

## Phạm vi
- Không thêm module PC/Mobile.
- Bổ sung AI Gateway phía backend.
- Kết nối Gemini Developer API theo cấu hình runtime `GEMINI_API_KEY`.
- Hỗ trợ thêm provider OpenAI-compatible qua biến môi trường, không khóa kiến trúc vào một nhà cung cấp.
- Controlled Self-Update: AI có thể phát hiện knowledge gap và tạo candidate; không tự ghi đè knowledge đã xuất bản.
- Provenance bắt buộc cho candidate lấy từ nguồn ngoài.
- API status/ask/knowledge-gap được đặt dưới `/api/v1/ai-connect/*` để các chức năng hiện có gọi lại mà không tạo UI/module mới.

## Cấu hình Gemini
`GEMINI_API_KEY` và tùy chọn `HDVIA_GEMINI_MODEL` được đọc ở runtime. Mặc định model là `gemini-2.5-flash-lite`.

## Luồng tự cập nhật
Question → Hành Trình AI → phát hiện thiếu dữ liệu → AI Gateway → candidate → validation/provenance → Knowledge Warehouse.

AI bên ngoài không có quyền tự publish trực tiếp.

## QA
Full regression suite: **165 passed**.

Focused AI Connect/Self-Update + routing/coverage tests: **20 passed**.

## Beta 1.23.1 Hardening
- Hành Trình AI có thể gọi AI Gateway để tạo knowledge candidate khi dữ liệu thiếu/độ tin cậy thấp; không thay thế các luồng live Weather/Route/Risk/Plan B.
- AI Connect yêu cầu đăng nhập + quyền `ai.assistant.use`, giới hạn 20 yêu cầu/phút và giới hạn kích thước prompt.
- Self-Update có hàng đợi `knowledge_update_jobs` và endpoint chạy có kiểm soát; hỗ trợ scheduler bằng `HDVIA_SELF_UPDATE_CRON_TOKEN`.
- GitHub Actions có workflow chạy Self-Update định kỳ mỗi ngày nếu đã cấu hình `HDVIA_SELF_UPDATE_URL` và `HDVIA_SELF_UPDATE_CRON_TOKEN`.
- Dữ liệu bên ngoài vẫn ở trạng thái CANDIDATE/REVIEW; không tự động ghi đè tri thức đã xác minh.
- PC/Mobile UI không thay đổi.
