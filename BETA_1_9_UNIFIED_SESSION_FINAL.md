# HDVIA Beta 1.9 — Unified Session Final

## Mục tiêu
Một lần đăng nhập cho toàn bộ HDVIA. Người dùng có thể chuyển giữa các module mà không phải đăng nhập lại; đăng xuất chủ động sẽ kết thúc phiên.

## Đã khóa
- Persistent Flask session trong thời hạn bảo mật 30 ngày, tự gia hạn khi hoạt động.
- Cùng một `uid`/identity snapshot được dùng xuyên suốt các module.
- `current_user()` ưu tiên dữ liệu tài khoản từ DB và có fallback identity snapshot khi instance serverless không còn DB runtime.
- Logout xóa toàn bộ session.
- Giữ nguyên RBAC/permission hiện có.
- Không thay đổi giao diện module ngoài yêu cầu phiên đăng nhập.

## Regression
- Existing Beta 1.9 test suite.
- Unified-session contract test.
- PC/mobile UI assets và route contracts được giữ nguyên.

## Lưu ý triển khai
Để phiên đăng nhập ổn định trên Vercel, biến môi trường `HDVIA_SECRET_KEY` phải được cấu hình bằng một giá trị cố định và `HDVIA_COOKIE_SECURE=1` cho production HTTPS.
