# HDVIA Beta 1.8.4
**Bạn Đồng Hành Du Lịch Việt Nam**

Nền tảng trợ lý thông minh cho Hướng dẫn viên Việt Nam.

## Quyền Beta
Người dùng đăng nhập bằng Google, Facebook hoặc Zalo được sử dụng đầy đủ chức năng Beta 1.8. Người dùng đã đăng nhập được viết bài tại Kho kinh nghiệm.

## Chạy
`python app.py`

## Kiểm thử
`pytest -q`

Xem `BETA_1_8_3_UI_RELEASE.md` và `BETA_1_8_3_OAUTH_DOMAINS_FIX.md` để biết phạm vi phát hành và cấu hình triển khai.

## Beta 1.8.4 Knowledge + Vietnamese UI Release
- Phiên bản hiện tại: `1.8.4-beta-knowledge-ui`
- Người dùng đăng nhập xã hội được dùng toàn bộ chức năng Beta.
- Kho kinh nghiệm có cơ chế duyệt trước khi công khai.
- Trợ lý AI Beta là trợ lý theo dữ liệu/chức năng HDVIA hiện có.

## Kho tri thức V1
- Phạm vi khởi đầu: Đà Nẵng – Hội An – Huế.
- Dữ liệu nằm trong `data/knowledge_base.json`.
- `knowledge_layer.py` thực hiện truy xuất theo từ khóa có trọng số.
- Đây là lớp truy xuất tri thức có kiểm duyệt, không phải quá trình huấn luyện lại mô hình AI.
- Trợ lý hành trình dùng kho tri thức này làm nguồn tham chiếu khi câu hỏi phù hợp.
