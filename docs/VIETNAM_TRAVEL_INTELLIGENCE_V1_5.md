# HDVIA Vietnam Travel Intelligence V1.5

V1.5 mở rộng phạm vi dữ liệu điểm đến từ tập trung miền Trung sang catalog điểm đến trên toàn Việt Nam, trong khi giữ nguyên các module bảo mật, Identity, Verified Guide và Journey Intelligence của V1.4.

## Phạm vi
- Destination Catalog toàn quốc (bản mẫu mở rộng)
- Tìm kiếm điểm đến theo tên/vùng
- Trang chi tiết điểm đến
- Kiến thức nền: overview, highlights, culture, history, food, best_for
- Tích hợp Weather Intelligence 7 ngày theo tọa độ điểm đến
- Tích hợp Destination Image Intelligence hiện có
- Journey Intelligence nhận diện thêm các điểm đến toàn quốc

## Kiến trúc
V1.4 Core → Vietnam Travel Intelligence Layer → Destination / Journey / Weather / Risk / Plan B.

Catalog hiện là lớp dữ liệu có cấu trúc, không phải dữ liệu huấn luyện LLM. Có thể tiếp tục mở rộng bằng dữ liệu được kiểm duyệt, API chính thống và knowledge graph.

## Lưu ý
Các nội dung trong catalog là lớp thông tin nền để thử nghiệm UI/logic. Trước production cần quy trình kiểm duyệt nguồn, versioning, provenance và cập nhật định kỳ.
