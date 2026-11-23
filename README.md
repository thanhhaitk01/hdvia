# HDVIA Beta 1.9 — Connect Foundation
**Bạn Đồng Hành Du Lịch Việt Nam**

Nền tảng trợ lý thông minh cho Hướng dẫn viên Việt Nam.

## Beta 1.9
Beta 1.9 kế thừa toàn bộ nền tảng Beta 1.8.5 và bổ sung **HDVIA Connect Foundation** — lớp trung tâm để HDVIA tích hợp các nền tảng bên ngoài mà không làm thay đổi Journey Intelligence, Knowledge Layer hoặc giao diện hiện tại.

### Connect Foundation
- `connect_core.py`: registry và metadata connector.
- `connectors.py`: lifecycle contract chung: `status`, `connect`, `callback`, `get_profile`, `disconnect`.
- `connect.py`: API `/api/v1/connect/status` và `/api/v1/connect/<provider>/status`.
- Google, Facebook và Zalo được quản lý qua cùng một Connect Registry.
- OAuth route thực tế hiện có vẫn nằm trong `oauth.py` và `app.py`.
- Client secret/token không được ghi vào source code hoặc API status.
- Profile/token synchronization với nền tảng bên ngoài **chưa được xem là hoàn tất trong Beta 1.9**; đây là bước tích hợp tiếp theo của Giai đoạn 1.

## Quyền Beta
Người dùng đăng nhập bằng Google, Facebook hoặc Zalo được sử dụng đầy đủ chức năng Beta. Người dùng đã đăng nhập được viết bài tại Kho kinh nghiệm.

## Chạy
`python app.py`

## Kiểm thử
`pytest -q`

Bản release phải đạt toàn bộ regression suite trước khi đưa lên GitHub/Vercel.

## Kho tri thức V1
- Phạm vi khởi đầu: Đà Nẵng – Hội An – Huế.
- Dữ liệu nằm trong `data/knowledge_base.json`.
- `knowledge_layer.py` thực hiện truy xuất theo từ khóa có trọng số.
- Đây là lớp truy xuất tri thức có kiểm duyệt, không phải quá trình huấn luyện lại mô hình AI.
- Trợ lý hành trình dùng kho tri thức này làm nguồn tham chiếu khi câu hỏi phù hợp.

## Meta / Facebook public URLs
- Chính sách quyền riêng tư: `/chinh-sach`
- Hướng dẫn xoá dữ liệu: `/xoa-du-lieu`
- Điều khoản sử dụng: `/dieu-khoan`

Khi cấu hình Meta, ghép các đường dẫn trên với domain public của HDVIA (ví dụ `https://hdvia.vn`). Không dùng URL giả hoặc URL localhost.
