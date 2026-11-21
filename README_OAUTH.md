# HDVIA OAuth Login Module V1.2 - Open Beta

## Mục tiêu
Giữ nguyên đăng nhập Email/Mật khẩu và bổ sung ngay bên dưới:
- Đăng nhập bằng Google
- Đăng nhập bằng Facebook

Trong Open Beta, OAuth user được phép truy cập hệ thống mà không yêu cầu Verified Guide/HDV approval.

## Cấu trúc
- `templates/login.html`: trang đăng nhập, đã include `oauth_buttons.html`
- `templates/oauth_buttons.html`: 2 nút Google/Facebook
- `templates/oauth_success.html`: trang thành công
- `auth/oauth.py`: OAuth routes và callback
- `static/oauth.css`: CSS cho cụm nút

## Tích hợp vào app.py hiện tại
Vì HDVIA hiện hữu có thể đã có `login`, `home` và session riêng, KHÔNG thay toàn bộ `app.py` bằng file mẫu.

Trong app khởi động Flask, thêm:

```python
from auth.oauth import init_oauth
init_oauth(app)
```

Nếu `app.py` đã có `login` và `home`, giữ nguyên các route đó.

Đảm bảo thư mục `auth/` có `__init__.py`.

## requirements
Thêm:

```text
Authlib>=1.3,<2
```

và cài lại requirements.

## Environment variables
Không đưa secret lên GitHub. Cấu hình ở Vercel/hosting:

```text
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
FACEBOOK_CLIENT_ID=...
FACEBOOK_CLIENT_SECRET=...
```

## Google Cloud
Authorized redirect URI phải trùng tuyệt đối với:

```text
https://<domain-HDVIА>/auth/callback/google
```

Ví dụ nếu domain chính là `https://hdvia.vn`:

```text
https://hdvia.vn/auth/callback/google
```

Nếu Vercel dùng domain preview, thêm redirect URI preview tương ứng khi cần test.

## Facebook
Callback URL:

```text
https://<domain-HDVIА>/auth/callback/facebook
```

## Quan trọng
Không commit `.env` hoặc client secret vào GitHub.

`login.html` trong gói này là mẫu tích hợp. Nếu file `login.html` hiện tại của HDVIA có giao diện/logic khác, chỉ cần chèn:

```jinja2
{% include "oauth_buttons.html" %}
```

ngay sau form đăng nhập, thay vì ghi đè toàn bộ file.
