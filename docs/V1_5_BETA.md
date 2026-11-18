# HDVIA V1.5 Beta — National Travel Intelligence + HDV Knowledge Hub

## Mục tiêu
V1.5 Beta mở rộng HDVIA từ phạm vi hành trình khu vực thành National Scope, đồng thời cho phép Verified Guide đóng góp bài viết, video, hình ảnh và kinh nghiệm thực địa. Nội dung được chuẩn hóa và lưu vào Central Travel Knowledge Store để tái sử dụng.

## Module mới
- HDV Knowledge Hub
- Verified Guide Contribution
- Knowledge Source Registry
- AI Knowledge Ingestion layer (provider-neutral)
- Wikipedia collector (beta)
- External source URL collector (beta, pending review)
- Knowledge confidence + source type
- Knowledge event/audit trail

## Nguyên tắc dữ liệu
1. Nội dung do Verified Guide tạo được gắn source_type=HDV_VERIFIED.
2. Dữ liệu bên ngoài được gắn source_type=EXTERNAL và trạng thái PENDING_REVIEW khi nạp tự động.
3. AI không tự cấp quyền Verified Guide và không tự duyệt dữ liệu nhạy cảm.
4. Mỗi knowledge item giữ nguồn, thời gian, tác giả và lịch sử sự kiện.
5. Không coi Wikipedia/Google là nguồn duy nhất hoặc tuyệt đối.

## External providers
- Wikipedia/Wikimedia: collector hoạt động ở beta.
- Google Places / Search: dành cho connector tiếp theo, cần API key và chính sách dữ liệu phù hợp.
- AI provider: kiến trúc không khóa model; hiện có local fallback để chạy thử không cần khóa API.

## Chạy local
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Mở `http://localhost:8000`.

## Demo admin
- Email: `admin@hdvia.local`
- Password mặc định: `ChangeMe123!` (đổi ngay khi triển khai thật)
