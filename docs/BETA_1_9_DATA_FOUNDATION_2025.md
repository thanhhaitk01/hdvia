# HDVIA Beta 1.9 — Data Foundation 2025

## Mục tiêu

Bổ sung lớp dữ liệu hành chính chuẩn cho HDVIA theo 34 đơn vị hành chính cấp tỉnh của Việt Nam áp dụng từ 01/07/2025, đồng thời tạo khóa liên kết để sau này nối điểm đến, thời tiết, hành trình và kho tri thức.

## Nguồn hành chính

- Nghị quyết 202/2025/QH15 về sắp xếp đơn vị hành chính cấp tỉnh.
- Quyết định 19/2025/QĐ-TTg về danh mục và mã số các đơn vị hành chính Việt Nam.

## Cấu trúc dữ liệu

1. `data/province_catalog_2025.json`: 34 tỉnh/thành, mã số, slug, vùng, tên gọi cũ dùng làm alias, đơn vị hình thành sau sắp xếp và các trung tâm du lịch gợi ý.
2. `destination_catalog.py`: giữ lớp điểm đến du lịch chi tiết hiện có, không trộn trực tiếp với lớp hành chính.
3. `data/knowledge_base.json`: giữ kho tri thức thuyết minh hiện có; các bài mới có thể gắn theo tỉnh/thành hoặc điểm đến ở giai đoạn tiếp theo.
4. `province_data.py`: lớp tra cứu thống nhất, hỗ trợ cả tên mới và tên cũ/alias.

## Nguyên tắc quan trọng

- Không dùng tên tỉnh cũ làm đơn vị hành chính hiện tại.
- Tên cũ vẫn được giữ làm alias để HDV có thể tìm kiếm theo cách gọi quen thuộc.
- Điểm đến du lịch là một lớp khác với tỉnh/thành; ví dụ Hội An vẫn là điểm đến nhưng được liên kết về thành phố Đà Nẵng trong lớp hành chính 2025.
- Mỗi tỉnh/thành có mã số chính thức làm khóa ổn định cho các lớp dữ liệu tiếp theo.

## API Beta 1.9

- `GET /api/v1/provinces`: trả về danh mục 34 tỉnh/thành.
- `GET /api/v1/provinces/<slug>`: tra cứu một tỉnh/thành theo slug, tên hoặc alias.

## Lộ trình kho dữ liệu tiếp theo

### Lớp 1 — Hành chính
34 tỉnh/thành → đã có trong Beta 1.9.

### Lớp 2 — Điểm đến
Tỉnh/thành → thành phố/thị xã/khu vực du lịch → điểm tham quan → tọa độ → ảnh → giờ mở cửa → phí → thời lượng tham quan.

### Lớp 3 — Tri thức HDV
Điểm đến → lịch sử → văn hóa → con người → kinh tế → ẩm thực → câu chuyện thuyết minh → lưu ý điều hành → nguồn kiểm chứng.

### Lớp 4 — Thời tiết & hành trình
Điểm tọa độ → dự báo → cảnh báo → ảnh hưởng lịch trình → phương án dự phòng.

### Lớp 5 — Kinh nghiệm HDV
Tình huống thực tế → kinh nghiệm → đánh giá → người đóng góp → trạng thái kiểm duyệt → phiên bản dữ liệu.

### Lớp 6 — Hình ảnh & tài nguyên
Mỗi điểm đến có `hero`, `gallery`, `thumbnail`, bản quyền/nguồn ảnh và trạng thái kiểm duyệt; không nên nhúng ảnh tùy tiện vào code.
