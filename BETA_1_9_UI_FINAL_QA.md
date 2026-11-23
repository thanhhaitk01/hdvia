# HDVIA Beta 1.9 — UI Final QA

## Mốc
Beta 1.9 — Master UI PC + Mobile

## Kiểm tra đã thực hiện
- Kiểm tra cấu trúc project và 22 template HTML.
- Kiểm tra cú pháp toàn bộ template bằng Jinja parser: PASS.
- Kiểm tra các route/chức năng chính được tham chiếu trong app và template.
- Kiểm tra lớp giao diện dùng chung: header, sidebar PC, mobile bottom navigation, đăng nhập, trang chủ, hành trình, kết quả, điểm đến, kho kinh nghiệm, trợ lý AI, kết nối, tài khoản/xác minh và quản trị.
- Bổ sung lớp CSS cuối cho Trợ lý AI và Kết nối & đồng bộ để tránh giao diện thiếu bố cục ở các trang này.
- `python -m compileall -q .`: PASS.
- `pytest -q`: 40/40 PASS.
- Loại bỏ `.pyc`, `.pyo`, `__pycache__`, `.pytest_cache`.

## Ghi chú
Môi trường kiểm tra hiện tại không có Flask runtime và không thể tải package từ Internet, nên không chạy được browser integration server trực tiếp trong môi trường này. Các kiểm tra runtime Flask cần được xác nhận thêm trên môi trường deploy/Vercel sau khi upload.
