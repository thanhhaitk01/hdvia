# HDVIA Beta 1.25.3.0 — 6 Layer Data Fusion

## Mục tiêu
Kết hợp mô hình 4 lớp và 5 tầng thành một pipeline thống nhất phía sau các module hiện có.

## 6 lớp
1. **Source Registry** — phân loại nguồn, quyền sử dụng, độ tin cậy, tần suất.
2. **Data Acquisition** — lấy dữ liệu có kiểm soát, chống trùng, giữ provenance, không tự động biến nguồn chưa duyệt thành tri thức chuẩn.
3. **Entity Resolution** — khóa địa điểm bằng tên chuẩn, alias, Wikidata, tọa độ và loại thực thể.
4. **Visual Resolution** — P18 → nguồn chính thống/được cấp phép → Openverse → Commons search/geosearch; chấm điểm và loại ảnh sai entity.
5. **Knowledge Fusion & Governance** — confidence, license, source, timestamp, trạng thái VERIFIED/CANDIDATE.
6. **HDVIA Knowledge Warehouse** — lưu knowledge/media metadata để Hành Trình AI dùng dữ liệu đã kiểm chứng.

## Quy tắc ảnh
- HTTP 200 không được xem là bằng chứng ảnh đúng.
- Ưu tiên độ chính xác hơn độ sẵn có.
- Nếu không đạt ngưỡng xác minh, không hiển thị ảnh đại diện.
- Ảnh phải có provenance; nếu có license metadata thì ghi nhận vào media warehouse.

## Nguồn mới
- Wikidata / Wikimedia Commons.
- Openverse cho lớp ảnh mở có thông tin license.
- Kho dữ liệu Du lịch số Quốc gia và Nền tảng số Du lịch Việt Nam được đăng ký như nguồn discovery/review, không tự ý sao chép nội dung khi chưa xác minh điều kiện tái sử dụng.
- Các nguồn thương mại/restricted không được coi là nguồn scraping tự do.

## QA
- Compile toàn bộ Python.
- Regression ảnh entity.
- Regression API connectivity.
- Regression Openverse fallback.
- Regression provenance/media warehouse.
