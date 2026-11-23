# HDVIA Beta 1.9 — Connect Foundation

## Mục tiêu
Xây lớp kết nối trung tâm để HDVIA có thể tích hợp các nền tảng bên ngoài mà không làm ảnh hưởng Journey Intelligence, Knowledge Layer hoặc giao diện Beta 1.8.5.

## Thành phần
- `connect_core.py`: registry và metadata connector.
- `connectors.py`: lifecycle contract chung cho connector bên ngoài: status, connect, callback, get_profile, disconnect.
- `connect.py`: API `/api/v1/connect/status` và `/api/v1/connect/<provider>/status`.
- OAuth Google/Facebook/Zalo hiện có được đưa vào Connect Registry.
- OAuth provider implementation thực tế vẫn dùng các route OAuth hiện có; Connect Foundation chưa tự động đồng bộ profile/token với nền tảng ngoài.

## Nguyên tắc
- Không lưu OAuth client secret trong mã nguồn.
- Không lưu OAuth token vào database HDVIA.
- API status chỉ trả metadata an toàn, không trả secret/token.
- Connector mới phải tuân theo lifecycle contract chung trước khi tích hợp.
- Không làm thay đổi Journey Intelligence, Knowledge Layer hoặc giao diện Beta 1.8.5.

## Kiểm tra
Chạy `pytest -q` để kiểm tra toàn bộ regression suite.
