# HDVIA Beta — Social Registration/Login

## Mục tiêu
Giai đoạn Beta tạm thời đóng đăng ký thành viên bằng form riêng. Người dùng truy cập `/login` và tạo/đăng nhập tài khoản bằng Google, Facebook hoặc Zalo.

## Luồng
1. Người dùng chọn Google / Facebook / Zalo.
2. HDVIA chuyển sang nhà cung cấp để xác thực.
3. Provider trả kết quả về callback của HDVIA.
4. HDVIA kiểm tra danh tính, tạo tài khoản USER nếu chưa có, hoặc liên kết với tài khoản hiện có theo email khi có email hợp lệ.
5. Hệ thống tạo session HDVIA và đưa người dùng về hồ sơ/chức năng họ đang mở.

## Bảo mật
- OAuth `state` được Authlib quản lý cho flow redirect.
- Không lưu mật khẩu của tài khoản Google/Facebook/Zalo.
- Token OAuth không lưu vào database của HDVIA.
- Mỗi provider có `provider_user_id` riêng trong bảng `social_accounts`.
- Email chỉ được dùng để liên kết với tài khoản hiện có khi provider cung cấp email.
- Tài khoản social mới mặc định `USER`, trust `L1` và `ACTIVE`.
- Xác thực Verified Guide vẫn tách riêng qua hồ sơ thẻ HDV; đăng nhập social không tự biến người dùng thành GUIDE.

## Cấu hình
Đặt các biến môi trường trong `.env`/hosting:
- `HDVIA_PUBLIC_BASE_URL`
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- `FACEBOOK_CLIENT_ID`, `FACEBOOK_CLIENT_SECRET`
- `ZALO_CLIENT_ID`, `ZALO_CLIENT_SECRET`

Callback URLs phải khai báo chính xác trong dashboard của từng provider.

## Beta behavior
`/register` được giữ lại để không phá URL cũ nhưng tự chuyển sang `/login`. Form đăng ký thủ công không còn được sử dụng cho thành viên mới.

## Tài khoản quản trị
Đăng nhập quản trị local vẫn tồn tại cho các tài khoản có `password_hash`. Public user không được tạo tài khoản local bằng form.
