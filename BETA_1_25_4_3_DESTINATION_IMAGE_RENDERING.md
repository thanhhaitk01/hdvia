# HDVIA Beta 1.25.4.4 — Destination Image Rendering Hardened

## Mục tiêu
Sửa lỗi giao diện điểm đến đã có dữ liệu ảnh nhưng vùng đại diện vẫn chỉ hiển thị placeholder/tên điểm.

## Thay đổi
- Bổ sung curated representative image registry cho các điểm lõi: Hà Nội, Hạ Long, Huế, Đà Nẵng, Hội An, Mỹ Sơn, Nha Trang, Đà Lạt.
- Ưu tiên ảnh đại diện đã có source/license/artist rõ ràng từ Wikimedia Commons.
- Hành Trình AI nhận `image_url`, `image_source_url`, `image_license`, `image_artist` trong `destination_context`.
- Frontend ưu tiên ảnh curated; nếu ảnh không tải được hoặc điểm chưa có ảnh curated thì fallback về `/api/v1/place-image`.
- Hiển thị nguồn/giấy phép/người chụp khi có metadata.
- Không thay đổi cấu trúc UI/module.

## QA
- Full suite: 34 passed, 8 subtests passed.
- Không phát hiện lỗi compile trong các test đã chạy.
- Test mới kiểm tra registry ảnh, truyền metadata vào destination context và fallback live image.
