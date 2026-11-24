# HDVIA Beta 1.11.0 — Open Data First

## Mục tiêu
Chuyển lớp dữ liệu bên ngoài của HDVIA sang kiến trúc open-data-first để không phụ thuộc Google Maps subscription cho chức năng dữ liệu địa điểm cơ bản.

## Đã tích hợp
- OpenStreetMap/Nominatim connector cho tra cứu địa điểm theo yêu cầu người dùng.
- GeoNames connector cho tra cứu địa danh; web service dùng tài khoản username miễn phí, đồng thời hỗ trợ hướng dùng dữ liệu tải xuống mở.
- Attribution/source metadata cho dữ liệu bên ngoài.
- API status và API search cho hai connector.
- Giữ nguyên External Gateway và Data Acquisition hiện có.
- Dữ liệu bên ngoài không được tự động publish: vẫn đi qua `CANDIDATE → REVIEW → PUBLISHED`.

## Quy tắc Nominatim
Không dùng public Nominatim cho autocomplete, bulk/systematic harvesting hoặc polling nền. Connector có rate-limit và attribution theo chính sách dịch vụ.

## Kiểm thử
- `90 passed`
- `python -m py_compile app.py open_data_connectors.py data_acquisition.py` — PASS
- Live external smoke test từ môi trường build không thực hiện được do môi trường hiện tại không phân giải DNS ra Internet; các connector đã có unit/integration contract tests với HTTP mock.
