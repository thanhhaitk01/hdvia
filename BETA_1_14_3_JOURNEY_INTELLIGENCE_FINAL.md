# HDVIA Beta 1.14.3 — Journey Intelligence Final

## Mục tiêu
Hoàn thiện lớp Hành Trình AI trên nền Beta 1.14.1, tập trung vào các lỗi phát hiện qua kiểm thử tương tác và hồi quy.

## Bổ sung chính
- Ambiguity Resolver được nối vào luồng phân tích: địa danh mơ hồ không bị tự đoán; trả về `pending_clarification` và validation `AMBIGUOUS_DESTINATION`.
- Natural Language Mutation mở rộng: đổi ngày, thay điểm, chuyển điểm, thêm điểm, bỏ điểm và các cách diễn đạt tự nhiên tương đương.
- Time Feasibility Engine: đối chiếu khung giờ khai báo với thời gian hoạt động + di chuyển + buffer, phát hiện `TIME_INFEASIBLE` / `TIME_TIGHT`.
- Start date mapping: khi có ngày khởi hành, Journey AI ánh xạ ngày tour sang ngày lịch thực để chọn forecast tương ứng trong 7 ngày.
- Mutation state được rebuild sạch, tránh text thừa sau khi bỏ/chuyển điểm.
- API Journey nhận `start_date`; câu hỏi tự nhiên có thể nhận ngày khởi hành dạng dd/mm/yyyy hoặc yyyy-mm-dd.
- Health/version contract cập nhật thành `1.14.3-vietnam-knowledge-hardening`.

## Kiểm thử
- Journey hardening + upgrade + conversation merge + template + safety + 1.14.3 regression: **23/23 PASS**.
- Toàn bộ suite ngoại trừ stress 1M: **104/104 PASS**.
- Stress suite 1M core iterations + 1,000 deterministic full analyses: **2/2 PASS**.
- Tổng regression test suite: **106/106 PASS** khi chạy các nhóm trên theo hai pha để tránh timeout của runner.

## Ghi chú
Route hiện tại vẫn là planning estimate dựa trên khoảng cách địa lý và tốc độ giả định; live road routing/traffic là bước nâng cấp tiếp theo, không được giả mạo là dữ liệu giao thông thực.
