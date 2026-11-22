# HDVIA V1.4 — Module Catalog

## 01. Identity & User Registration
- Register / Login / Logout / Profile
- USER role mặc định
- Trust L1
- Permission theo role

## 02. Verified Guide Registration
- Chọn “Tôi là Hướng dẫn viên du lịch”
- Mã số thẻ HDV
- Loại thẻ
- Ảnh thẻ
- Khu vực hoạt động
- Ngôn ngữ
- Trạng thái PENDING_REVIEW

## 03. Guide Verification
- Admin Dashboard
- Xem hồ sơ và ảnh thẻ
- APPROVE / REJECT / NEED_MORE_INFORMATION
- Admin là thẩm quyền cuối cùng
- APPROVE → GUIDE + Trust L2
- AI/OCR chỉ hỗ trợ, không tự xác minh

## 04. Permission & Zero Trust
Identity → Verification → Admin Approval → Role → Trust → Permission → Access.
- Least privilege
- Permission checks ở route
- Sensitive identity data không mở cho agent tùy ý

## 05. Audit Log
- User ID / Admin ID
- Action
- Target
- Previous/new workflow action
- Timestamp
- IP metadata
- Review history

## 06. Journey Intelligence
- Nhập lịch trình
- Parse theo ngày
- Nhận diện điểm đến
- Tính khoảng cách
- Route summary
- Lưu lịch sử
- JSON API

## 07. Weather Intelligence
- Weather provider Open-Meteo
- 7 ngày theo từng điểm
- Nhiệt độ min/max
- Mưa
- Gió
- Mã thời tiết
- Endpoint live `/api/v1/weather`

## 08. Risk Engine
- LOW / MEDIUM / HIGH / UNKNOWN
- Mưa, gió, nắng nóng, hiện tượng mạnh
- Khuyến nghị hành động

## 09. Plan B
- Cảnh báo hoạt động ngoài trời
- Khuyến nghị đổi thứ tự/giãn buffer
- Hướng dẫn chuẩn bị phương án thay thế

## 10. Destination Image Intelligence
- Nhận diện tên điểm trong hành trình
- Tìm ảnh theo điểm qua Wikimedia Commons API
- Hiển thị ảnh trong Journey Dashboard
- Có fallback khi nguồn ảnh không khả dụng

## 11. Live Travel Dashboard
- Timeline từng ngày
- Ảnh điểm đến
- Thời tiết hiện tại + 7 ngày
- Risk badge
- Route summary
- Plan B
- Cập nhật lại dữ liệu bằng nút phân tích
- Responsive desktop/mobile

## 12. API & Operations
- `/health`
- `/api/v1/journey/analyze`
- `/api/v1/weather`
- `/api/v1/place-image`
- `/api/v1/route`

## 13. Security Baseline
- Session HTTPOnly
- SameSite
- Protected guide-card image
- Role/permission checks
- Audit logging
- Environment secret
- Production hardening documented

## 14. Roadmap modules
Nền móng đã chuẩn bị cho Knowledge Layer → AI Assistant → AI Copilot → AI Agent → Travel Intelligence → Tourism Intelligence Platform.
