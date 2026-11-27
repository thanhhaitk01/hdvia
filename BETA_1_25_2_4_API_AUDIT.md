# HDVIA Beta 1.25.2.4 — API Connectivity + Live Data Audit

## Chốt

- Connectivity smoke check mở rộng lên 10 nguồn: Weather, Geocoding, Routing, Air Quality, Marine, OSM, Wikipedia, Wikidata, Sunrise/Sunset, Wikimedia Commons Image.
- Có trạng thái `LIVE`, `CACHE`, `ERROR` và `freshness` với `fetched_at`, `age_seconds`, `ttl_seconds`.
- Cache TTL được tách theo loại dữ liệu; weather/marine 5 phút, air quality 10 phút, routing 15 phút, ảnh 6 giờ, knowledge/OSM/geocode 24 giờ.
- Live routing được bật mặc định qua `.env.example`; production có thể override bằng biến môi trường.
- Ảnh điểm đến dùng cùng lớp adapter + cache thay vì endpoint gọi provider riêng lẻ.
- JavaScript ảnh của Journey AI được đưa ra khỏi `<title>` và chạy ở block scripts cuối trang.

## Health endpoint

`GET /api/v1/public-api/connectivity?place=Chùa%20Cầu%20Hội%20An&lat=15.8777&lon=108.3268`

Endpoint này là smoke test đọc-only; nó kiểm tra khả năng runtime đang deploy kết nối tới provider tại thời điểm gọi.

## Ý nghĩa freshness

- `LIVE`: vừa gọi provider và nhận dữ liệu thành công.
- `CACHE`: dùng dữ liệu đã lấy trước đó nhưng còn trong TTL.
- `ERROR`: provider không trả dữ liệu thành công.

`CACHE` không có nghĩa dữ liệu đã cũ ngoài TTL; nó nghĩa HDVIA đang dùng bản cache còn hạn.

## Lưu ý

Dữ liệu live không được hiểu là provider cập nhật từng giây. Open-Meteo cho biết các model thường được cập nhật vài giờ một lần và khuyến nghị chờ thêm sau khi model mới phát hành; vì vậy HDVIA dùng TTL để lấy dữ liệu mới khi cần thay vì polling liên tục.
