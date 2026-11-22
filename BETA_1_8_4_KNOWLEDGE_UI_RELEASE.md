# HDVIA Beta 1.8.4 — Knowledge + Vietnamese UI

## Mục tiêu
Kế thừa Beta 1.8.3 Stable Baseline, tập trung vào hai thay đổi: tinh gọn giao diện tiếng Việt và bổ sung Knowledge Layer V1.

## UI
- Bỏ dòng giới thiệu `TRỢ LÝ AI CHUYÊN BIỆT CHO HƯỚNG DẪN VIÊN VIỆT NAM`.
- Bỏ tiêu đề `Trí tuệ đồng hành, hành trình chủ động.`.
- Đổi nhãn hiển thị `Trợ lý AI` thành `Trợ lý hành trình` ở các vị trí giao diện chính.
- Giữ nguyên route backend `/tro-ly-ai` để tránh phá tương thích.

## Knowledge Layer V1
- Phạm vi seed: Đà Nẵng, Hội An, Huế và tuyến kết hợp Đà Nẵng – Hội An – Huế.
- Dữ liệu có cấu trúc theo điểm đến, nhóm kiến thức, tóm tắt, nội dung và từ khóa.
- Có lớp truy xuất `knowledge_layer.py` với cơ chế chấm điểm minh bạch.
- Trợ lý hành trình dùng kho tri thức làm nguồn tham chiếu khi câu hỏi phù hợp.
- Đây là retrieval từ dữ liệu được quản lý, **không phải huấn luyện lại mô hình AI**.

## Bảo toàn
- Không thay đổi RBAC/role hiện có.
- Không thay đổi Journey Intelligence contract.
- Không thay đổi các route OAuth hiện có.
- SQLite runtime và các giới hạn Beta của 1.8.3 vẫn được giữ nguyên.
