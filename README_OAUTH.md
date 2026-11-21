# HDVIA Quick Login Module V1.1 — OPEN BETA

## Mục tiêu bản Beta
Trong giai đoạn thử nghiệm, HDVIA tạm thời KHÔNG yêu cầu xác thực giấy phép HDV để truy cập.

Tất cả người dùng có thể:
- Đăng nhập nhanh bằng Google.
- Đăng nhập nhanh bằng Facebook.
- Truy cập các chức năng HDVIA đang được mở trong bản Beta.

Cơ chế xác thực/đăng ký HDV chính thức được tạm đóng trong giai đoạn thu thập dữ liệu và kiểm thử. Khi HDVIA chuyển sang bản chính thức, có thể bật lại Verified Guide / phân quyền.

## OAuth endpoints
- Google login: /auth/login/google
- Google callback: /auth/callback/google
- Facebook login: /auth/login/facebook
- Facebook callback: /auth/callback/facebook

## Environment
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
FACEBOOK_APP_ID
FACEBOOK_APP_SECRET
HDVIA_BASE_URL=https://hdvia.vn
SESSION_SECRET=CHANGE_ME
HDVIA_AUTH_MODE=open_beta

Không lưu Client Secret trực tiếp trong GitHub.

## Tích hợp
Trong app Flask hiện tại:
1. init_oauth(app)
2. register oauth_bp
3. đưa templates/oauth_buttons.html vào trang đăng nhập.

Module này KHÔNG tự thay thế database/user system hiện hữu của HDVIA.
Để đồng bộ người dùng OAuth vào database HDVIA, cần nối hàm tạo/tìm user với database hiện tại.
