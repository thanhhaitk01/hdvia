# HDVIA Beta 1.8.1 – Commercial Trial

## Mục tiêu
Bản thử nghiệm thương mại để đưa HDVIA ra cho người dùng thật trải nghiệm và bắt đầu thu thập dữ liệu.

## Đã bổ sung
- Giữ nguyên logo HDVIA và slogan: **Trí tuệ đồng hành, hành trình chủ động.**
- Giữ giao diện người dùng tiếng Việt.
- Trang chủ chuyển thành landing page hướng trải nghiệm thật, có CTA đăng nhập miễn phí.
- Bổ sung màn hình **Trợ lý AI** với các nhóm hỗ trợ về hành trình, thời tiết/cảnh báo, thuyết minh và xử lý tình huống. Đây là trợ lý Beta theo dữ liệu/chức năng HDVIA hiện có, không giả lập một mô hình ngôn ngữ bên ngoài.
- Bổ sung Điều khoản sử dụng và Chính sách dữ liệu.
- Bổ sung cơ chế CSRF cho các thao tác POST chính.
- Bổ sung bảng dữ liệu `knowledge_posts` trong khởi tạo CSDL; Beta 1.8 trước đó thiếu bảng này dù đã có route Kho kinh nghiệm.
- Bài viết Kho kinh nghiệm được đưa về trạng thái `PENDING_REVIEW` trước khi công khai; quản trị viên có màn hình duyệt/từ chối.
- Bổ sung quản trị Kho kinh nghiệm.
- Phiên bản hệ thống: `1.8.1-beta-commercial`.
- Journey Engine: `1.8.1`.

## Kiểm thử
- Pytest: **24/24 PASS**.
- Stress test lõi: **1.000.000 lượt PASS**.
- Phân tích hành trình deterministic đầy đủ: **1.000 lượt PASS**.
- Compileall: **PASS**.
- AST toàn bộ Python: **PASS**.
- Logo + slogan + giao diện Việt hóa: **PASS** theo test hợp đồng.

## Giới hạn cần kiểm tra sau deploy
- Môi trường build hiện tại không có Flask/Authlib nên không thể chạy Flask production smoke test tại đây.
- OAuth Google/Facebook/Zalo phải được smoke-test trên Vercel bằng credentials thực tế.
- SQLite đặt trong `/tmp` là bộ nhớ tạm của môi trường serverless. Nếu chạy quảng cáo và có người dùng thật, cần cấu hình **CSDL bên ngoài có lưu trữ bền vững** trước khi coi dữ liệu người dùng là dữ liệu sản phẩm chính thức.

## Nguyên tắc quảng cáo
Chỉ quảng cáo các chức năng đã có thật trong bản này: phân tích hành trình, thời tiết 7 ngày, cảnh báo rủi ro, lộ trình & khoảng cách, thuyết minh, phương án dự phòng, điểm đến, Kho kinh nghiệm và Trợ lý AI Beta.
