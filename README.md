# HDVIA — AI Travel Intelligence Platform
## FULL V1.4.0 — OFFICIAL OVERWRITE BUILD

Bản hợp nhất nâng cấp từ V1.3, giữ nguyên các module Identity/Verified Guide/Journey Intelligence và thay giao diện chính bằng Live Travel Intelligence Dashboard.

### Đã tích hợp
1. User Registration / Login / Profile.
2. USER / GUIDE / PARTNER / ADMIN / SUPER_ADMIN roles.
3. Trust L0–L4; approved guide → L2.
4. Guide Registration: card number + card type + card image + area + languages.
5. PENDING_REVIEW workflow.
6. Admin final authority: APPROVE / REJECT / NEED_MORE_INFORMATION.
7. APPROVE → GUIDE + L2.
8. Role/Permission + least privilege.
9. Audit Log.
10. Protected guide-card images.
11. Zero Trust baseline.
12. Journey parser + destination recognition.
13. Distance / route summary.
14. 7-day weather per destination.
15. Live weather API endpoint using Open-Meteo provider.
16. Risk LOW / MEDIUM / HIGH / UNKNOWN.
17. Plan B recommendations.
18. Destination image lookup via Wikimedia Commons API with fallback.
19. New Live Travel Intelligence Dashboard.
20. Journey history.
21. API `/api/v1/journey/analyze`.
22. API `/api/v1/weather`.
23. API `/api/v1/place-image`.
24. API `/api/v1/route`.
25. `/health`.
26. Dockerfile + docker-compose.
27. Documentation: architecture, security, module catalog, deployment.

### Luồng Verified Guide chính thức
Identity → Verification → Admin Approval → Role → Trust → Permission → Access.

AI/OCR chỉ được hỗ trợ kiểm tra. Không có logic tự động cấp Verified Guide.

### Giao diện chính
Live Travel Intelligence Dashboard gồm:
- Timeline từng ngày
- Ảnh địa điểm
- Thời tiết hiện tại
- 7 ngày thời tiết
- Cảnh báo mưa/gió/nhiệt độ
- Risk badge
- Bản đồ/tuyến hành trình placeholder sẵn sàng tích hợp map provider
- Kết luận AI
- Plan B

### Chạy local
python -m venv .venv

Windows:
.venv\\Scripts\\activate

macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python app.py

Mở http://127.0.0.1:8000

Demo admin:
email: admin@hdvia.local
password: ChangeMe123!

Đổi mật khẩu demo trước khi public.

### Ghi đè GitHub
Giải nén ZIP. Lấy toàn bộ nội dung bên trong thư mục `HDVIA_FULL_V1_4/` ghi đè vào root repository `hdvia` hiện tại. Không upload ZIP như một thư mục ứng dụng. Giữ thư mục `.git` nếu thao tác bằng local Git.

### Production
Trước khi public:
- HTTPS
- production secret
- PostgreSQL/MySQL
- OTP/MFA thật
- private object storage cho ảnh thẻ
- rate limiting / CSRF / WAF
- monitoring / backup / recovery
- secret management
- quyền truy cập dữ liệu du lịch chính thức
- AI Security Gate cho Agent/Tool

Chi tiết module xem `docs/MODULE_CATALOG_V1_4.md`.
