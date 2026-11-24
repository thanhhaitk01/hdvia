# HDVIA 1.11.0 — Open Data Agent

## Mục tiêu
HDVIA có một tác vụ thu thập dữ liệu tự động từ các nguồn mở/miễn phí đã được đăng ký trong `source_registry.py`.

## Nguồn được bật
- Wikimedia/Wikipedia tiếng Việt: API chính thức, lưu nội dung dưới dạng CANDIDATE kèm license/attribution.
- OpenStreetMap Nominatim: geocoding giới hạn, có cache/inbox và attribution ODbL.

Nguồn bị hạn chế không được thêm vào danh sách tự động. Agent không scrape Vietravel, Saigontourist, Vietnam.travel hoặc các website tương tự nếu điều khoản không cho phép.

## Cách chạy tự động
GitHub Actions chạy mỗi ngày lúc `00:30 UTC` và có thể chạy thủ công bằng `workflow_dispatch`. Sau khi thu thập, agent commit `data/acquisition/candidates.json` nếu có dữ liệu mới.

## An toàn dữ liệu
Luồng là:

`OPEN SOURCE → ACQUISITION AGENT → CANDIDATE → REVIEW/VALIDATE → PUBLISHED`

Agent tuyệt đối không tự publish vào kho dữ liệu đang phục vụ người dùng.

## Lưu ý vận hành
Nominatim public server có giới hạn tải; HDVIA chỉ dùng số lượng request rất nhỏ mỗi lần chạy. Nếu quy mô tăng, chuyển sang instance/provider OSM phù hợp thay vì tăng tải lên máy chủ công cộng.
