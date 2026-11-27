# HDVIA Beta 1.25.8 — Place Weather Intelligence

## Mục tiêu
Khi HDV nhập một điểm bất kỳ vào Hành Trình AI, HDVIA phải liên kết điểm đó với tọa độ thực tế, ngữ cảnh hành chính cấp xã khi nguồn bản đồ cung cấp, dự báo thời tiết 7 ngày, rủi ro thời tiết và hành động chuẩn bị cho HDV/khách.

## Luồng
`Điểm nhập` → `Entity/Deep Research` → `tọa độ điểm` → `cấp xã/địa phương` → `thời tiết 7 ngày` → `đánh giá mưa/gió/nắng/dông` → `hành trang + Plan B` → `Weather Watch`.

## 24/7
- Mỗi lần truy vấn: lấy/cập nhật forecast theo TTL live.
- Mỗi điểm đã xuất hiện trong Hành Trình AI được đăng ký vào `weather_watch_points`.
- GitHub Actions `HDVIA Weather Watch 24/7` gọi refresh định kỳ 15 phút.
- Cần cấu hình `HDVIA_SELF_UPDATE_URL` và `HDVIA_WEATHER_WATCH_TOKEN` trên GitHub/Vercel.

## Ranh giới an toàn dữ liệu
Cảnh báo mưa/gió/nhiệt/dông trong bản này là cảnh báo suy luận từ dữ liệu thời tiết. Cảnh báo thiên tai chính thức phải được nối với nguồn cảnh báo có thẩm quyền khi connector tương ứng được cấu hình; không tự gắn nhãn cảnh báo chính thức.
