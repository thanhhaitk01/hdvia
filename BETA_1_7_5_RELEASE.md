# HDVIA Beta 1.7.5 — Release

## Giữ nguyên
- Giao diện Beta 1.6.
- Journey Intelligence, Tour Briefing, Plan B, feedback.
- 7 ngày thời tiết theo từng điểm nhận diện được.
- Google/Facebook/Zalo social login khi provider được cấu hình.
- Chưa bật xác thực HDV tự động; hồ sơ xác minh vẫn là quy trình riêng.
- Destination catalog, route intelligence, profile và admin guide review.

## Nâng cấp 1.7.5
- Chuẩn hóa build/version thành 1.7.5-beta.
- Bổ sung response hardening: no-cache cho HTML/API và security headers.
- Thêm `/__version` để kiểm tra deployment đang chạy đúng build.
- Health endpoint liệt kê rõ các module cốt lõi.
- Journey Engine nâng version 1.7.5.
- Bổ sung lớp kiểm tra chất lượng lịch trình (`quality.score`, `quality.flags`) nhưng không phá contract cũ.

## Không đưa vào Beta 1.7.5
- Không bật xác thực giấy phép HDV tự động.
- Không thay đổi giao diện hiện tại.
- Không thêm hệ thống AI cloud mới hoặc API key bắt buộc.
- Không thay đổi cơ chế Google sync login.
