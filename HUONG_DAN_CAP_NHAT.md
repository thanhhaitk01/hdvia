# HDVIA 1.5.1 Beta — Cập nhật định hướng mở

## Mục tiêu
Bản cập nhật này chuyển HDVIA sang giai đoạn thử nghiệm mở:
- Người dùng thông thường được sử dụng các chức năng cốt lõi.
- Không bắt buộc xác thực hướng dẫn viên trong giai đoạn thử nghiệm.
- Người dùng được phép đóng góp tri thức; nội dung mới được đưa vào trạng thái chờ kiểm tra trước khi trở thành tri thức chung.
- Giao diện và thông báo hướng tới tiếng Việt dễ hiểu.
- Giữ nguyên nền xác thực hướng dẫn viên để kích hoạt ở giai đoạn sau.
- Định hướng đăng nhập bằng Google, Facebook và Zalo được xác định là phương thức đăng nhập xã hội cho giai đoạn tiếp theo; việc kết nối thực tế cần khóa ứng dụng và thông tin cấu hình của từng nhà cung cấp.

## Thay đổi kỹ thuật trong gói này
- Nâng phiên bản từ 1.5.0-beta lên 1.5.1-beta.
- Người dùng thường được cấp quyền đọc và gửi đóng góp cho kho tri thức.
- Đóng góp của người dùng không còn được gắn nhãn là nội dung đã xác thực; chuyển sang trạng thái `PENDING_REVIEW`.
- Thêm `/api/v1/policy` để công bố chính sách giai đoạn thử nghiệm.
- `/health` trả thêm trạng thái xác thực hướng dẫn viên chưa bắt buộc.
- Giữ nguyên bảng hồ sơ xác thực hướng dẫn viên và quy trình quản trị để dùng ở giai đoạn sau.

## Lưu ý
Gói này là **gói cập nhật phần lõi** dựa trên `app.py` hiện có trong HDVIA V1.5. Nó không thay thế toàn bộ mã nguồn/templates của dự án.

Đăng nhập Google/Facebook/Zalo cần được nối vào phần giao diện và thông tin cấu hình của từng nhà cung cấp khi sếp triển khai lên máy chủ. Không nên giả lập đăng nhập xã hội trong bản thử nghiệm.
