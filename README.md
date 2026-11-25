# HDVIA Beta 1.14.3 — Vietnam Knowledge Hardening
**Bạn Đồng Hành Du Lịch Việt Nam**

Release baseline: `1.14.3-vietnam-knowledge-hardening`
**Bạn Đồng Hành Du Lịch Việt Nam**

Nền tảng trợ lý thông minh cho Hướng dẫn viên Việt Nam.

## Beta 1.14.3
Beta 1.14.3 kế thừa nền tảng Connect/Journey/Conversation và bổ sung **Vietnam Knowledge Hardening** — lớp bảo vệ để phân biệt địa điểm được nhận diện với tri thức đã được kiểm duyệt, đồng thời mở rộng coverage điểm du lịch Việt Nam.

### Connect Foundation
- `connect_core.py`: registry và metadata connector.
- `connectors.py`: lifecycle contract chung: `status`, `connect`, `callback`, `get_profile`, `disconnect`.
- `connect.py`: API `/api/v1/connect/status` và `/api/v1/connect/<provider>/status`.
- Google, Facebook và Zalo được quản lý qua cùng một Connect Registry.
- OAuth route thực tế hiện có vẫn nằm trong `oauth.py` và `app.py`.
- Client secret/token không được ghi vào source code hoặc API status.
- Trang hướng dẫn xóa dữ liệu công khai: `/data-deletion` (đồng thời hỗ trợ `/data_deletion`) để dùng làm Data Deletion Instructions URL cho nhà cung cấp đăng nhập bên ngoài.
- Profile/token synchronization với nền tảng bên ngoài **chưa được xem là hoàn tất trong Beta 1.9**; đây là bước tích hợp tiếp theo của Giai đoạn 1.

## Quyền Beta
Người dùng đăng nhập bằng Google, Facebook hoặc Zalo được sử dụng đầy đủ chức năng Beta. Người dùng đã đăng nhập được viết bài tại Kho kinh nghiệm.

## Chạy
`python app.py`

## Kiểm thử
`pytest -q`

Bản release phải đạt regression suite; stress suite được chạy riêng và ghi nhận kết quả trong release validation.

## Kho tri thức V1
- Phạm vi khởi đầu: Đà Nẵng – Hội An – Huế.
- Dữ liệu nằm trong `data/knowledge_base.json`.
- `knowledge_layer.py` thực hiện truy xuất theo từ khóa có trọng số.
- Đây là lớp truy xuất tri thức có kiểm duyệt, không phải quá trình huấn luyện lại mô hình AI.
- Trợ lý hành trình dùng kho tri thức này làm nguồn tham chiếu khi câu hỏi phù hợp.


## Beta 1.10.10
- Controlled external Data Acquisition: web/API/Google CSE connector.
- External records enter CANDIDATE with Lineage; no auto-publish.
- Data Core remains the orchestration layer for the 8 warehouses.
