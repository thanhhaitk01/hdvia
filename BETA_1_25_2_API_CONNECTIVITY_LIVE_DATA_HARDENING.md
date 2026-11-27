# HDVIA Beta 1.25.2 — API Connectivity & Live Data Hardening

## Mục tiêu
Audit và làm cứng chuỗi kết nối API: provider bên ngoài → adapter HDVIA → dữ liệu → giao diện.
Không thêm module giao diện.

## Đã kiểm tra/sửa
- Thêm `GET /api/v1/public-api/connectivity` để smoke-test live các provider: weather, geocoding, routing, air quality, marine, OSM, Wikipedia, Wikidata, sunrise/sunset.
- `public-api/health` tiếp tục báo cấu hình; `connectivity` mới kiểm tra khả năng gọi provider thật khi chạy trên môi trường deploy.
- Air quality và marine public endpoints dùng chung OpenAPIAdapter/cache thay vì gọi trực tiếp provider.
- Ảnh đại diện Wikimedia trả trạng thái lỗi rõ ràng (`502` khi provider unreachable, `404` khi không có ảnh), kèm source/source_url; không còn im lặng thất bại.
- Giao diện ảnh đại diện ghi trạng thái lỗi và không giữ broken-image.
- Phiên bản runtime thống nhất 1.25.2.

## Regression
191/191 tests PASS.

## Giới hạn kiểm tra môi trường hiện tại
Môi trường build này không phân giải DNS ra Internet (`Temporary failure in name resolution`), nên không thể dùng nó để tuyên bố các provider bên ngoài đang trả dữ liệu live. Đây là lý do bản 1.25.2 bổ sung endpoint connectivity để kiểm tra ngay trên môi trường Vercel sau deploy.
