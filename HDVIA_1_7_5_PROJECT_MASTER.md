# HDVIA — PROJECT MASTER / BETA 1.7.5

## 1. Mục tiêu gốc
HDVIA là AI Travel Intelligence dành cho Hướng Dẫn Viên Việt Nam, tập trung vào phân tích hành trình, dữ liệu điểm đến, thời tiết, rủi ro, briefing cho HDV và phương án Plan B.

## 2. Định hướng không thay đổi
- Thị trường: Việt Nam trước, có khả năng mở rộng quốc tế.
- Nền tảng: Web trước; kiến trúc giữ khả năng mở rộng mobile.
- Quyền truy cập: giai đoạn Beta chưa tự động xác thực giấy phép HDV.
- Đăng nhập: giữ social sync Google; Facebook/Zalo vẫn hỗ trợ khi được cấu hình.
- Giao diện: giữ giao diện Beta hiện tại.
- Core: Journey Intelligence + 7-day weather + risk + Tour Briefing + Plan B + destination intelligence + feedback.

## 3. Tình trạng Beta 1.7.5
### Đã có và kiểm tra
- Flask/Vercel zero-config entrypoint `app.py`.
- Google/Facebook/Zalo OAuth module.
- Social account sync vào user hiện có.
- Profile và hồ sơ đăng ký xác minh HDV (chưa tự động cấp quyền).
- Destination catalog Việt Nam.
- Journey parser nhận diện ngày/điểm.
- 7 ngày thời tiết cho từng điểm nhận diện.
- Risk map LOW/MEDIUM/HIGH.
- Route distance intelligence.
- Tour Briefing.
- Plan B theo ngày.
- Journey feedback.
- Admin guide review/audit.
- Cache hardening + security headers.
- `/health` và `/__version` để kiểm tra deployment.
- Quality layer cho lịch trình: `quality.score` + `quality.flags`.

## 4. Những thứ KHÔNG bật trong 1.7.5
- Không tự động xác thực giấy phép HDV.
- Không ép người dùng đăng ký thành viên riêng.
- Không đổi UI.
- Không phụ thuộc API AI trả phí để Journey Intelligence hoạt động.
- Không đưa feedback trực tiếp vào Knowledge Base.

## 5. Cần bổ sung ở các bản tiếp theo
### Ưu tiên P0
1. Test integration thật trên Vercel với biến môi trường OAuth.
2. Kiểm tra domain `hdvia.vn` và `www.hdvia.vn`/redirect canonical.
3. Google Search Console + sitemap + robots + metadata/OG.
4. Cơ chế lưu dữ liệu bền vững thay cho SQLite `/tmp` khi có người dùng thật.

### Ưu tiên P1
1. Knowledge Base có nguồn và versioning.
2. Guide Copilot có AI model thật, có kiểm soát nguồn.
3. Itinerary optimizer: thời gian, khoảng cách, buffer, thứ tự điểm.
4. Weather alert theo lịch tour.
5. Tour brief đa ngôn ngữ.
6. Export briefing/itinerary.

### Ưu tiên P2
1. Mobile/PWA.
2. Analytics sản phẩm.
3. Verified Guide badge sau khi có quy trình xác minh pháp lý/vận hành ổn định.
4. Partner marketplace.

## 6. Những thứ cần tránh
- Không chồng nhiều bản `app.py` lên nhau.
- Không commit ZIP/source tạm vào repository production.
- Không sửa trực tiếp production khi chưa chạy test.
- Không thêm module không có dependency vào `app.py`.
- Không triển khai tính năng xác thực HDV khi quy trình và dữ liệu xác minh chưa sẵn sàng.

## 7. Quy trình release chuẩn từ 1.7.5
1. Source sạch.
2. `pytest` PASS.
3. `compileall` PASS.
4. Engine offline smoke PASS.
5. Kiểm tra cấu trúc Vercel.
6. GitHub repository sạch.
7. Commit duy nhất cho release.
8. Vercel deploy.
9. Smoke test production: `/health`, `/__version`, `/`, `/login`, `/destinations`, `/journey`, weather, Journey API.
10. Chỉ sau khi production PASS mới tăng version tiếp theo.
