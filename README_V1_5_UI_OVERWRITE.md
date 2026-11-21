# HDVIA V1.5 — UI OVERWRITE PACKAGE

Bản này giữ nguyên backend/module V1.4 + lớp Vietnam Travel Intelligence V1.5 hiện có, đồng thời thay lớp giao diện web chính sang **HDVIA V1.5 Live Travel Intelligence**.

## Đã thay đổi giao diện
- Header/nav mới theo hướng Travel Intelligence.
- Trang chủ mới: hero HDVIA, nhập hành trình, Live Travel Intelligence, Weather Intelligence, Verified Guide, Risk/Plan B, AI Copilot.
- Responsive desktop/mobile.
- Giữ các route/backend hiện có; không thay đổi luồng Identity, Verified Guide, Admin, Audit, Journey API.

## Đưa lên GitHub
Ghi đè nội dung repository `thanhhaitk01/hdvia` bằng toàn bộ nội dung thư mục này, sau đó commit message:
`HDVIA V1.5 — Live Travel Intelligence UI`

## Lưu ý
Gói này không chứa database runtime hoặc private uploads.

## Cập nhật Beta — Social Registration/Login
- Đóng đăng ký thành viên bằng form riêng.
- Người dùng đăng nhập/đăng ký nhanh bằng Google, Facebook hoặc Zalo.
- Thêm bảng liên kết `social_accounts`.
- Tài khoản social mới mặc định USER/L1/ACTIVE.
- Verified Guide vẫn qua luồng xét duyệt thẻ HDV riêng.
- `/register` redirect về `/login` để giữ tương thích URL cũ.
