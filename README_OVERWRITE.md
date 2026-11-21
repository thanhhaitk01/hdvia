# HDVIA OAuth overwrite package

Ghi đè các file theo đúng đường dẫn trong ZIP vào repository `hdvia`, branch `main`.

Các file trong gói:
- `app.py` — bản đầy đủ hiện tại, đã tích hợp `init_oauth(app)`.
- `auth/oauth.py` — đăng ký Google/Facebook OAuth.
- `auth/__init__.py`
- `templates/login.html` — hiển thị Đăng nhập nhanh ngay dưới nút Đăng nhập.
- `templates/oauth_buttons.html` — endpoint đúng `oauth.oauth_login`.
- `templates/oauth_success.html`
- `requirements.txt` — bổ sung Authlib và requests.

Biến môi trường cần có trên Vercel:
- GOOGLE_CLIENT_ID
- GOOGLE_CLIENT_SECRET
- FACEBOOK_CLIENT_ID
- FACEBOOK_CLIENT_SECRET
- HDVIA_SECRET_KEY

Sau khi upload/ghi đè, Vercel cần deploy lại branch `main`.
