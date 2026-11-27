# HDVIA Beta 1.30.1 — HDV Giàu Kinh Nghiệm

Bản này nâng Travel Intelligence Brain thành lớp hỗ trợ kinh nghiệm thực chiến cho HDV, vẫn giữ Hành Trình AI là điểm vào chính và không tạo module giao diện mới.

## Các lớp chính
- Travel Ontology đa nhãn
- Travel Story Graph
- HDV Experience Brief
- Guide Decision Engine
- HDV Experience Memory: tình huống → bài học → hành động
- Route/Time Decision: thời gian → quãng đường → thời lượng → buffer → phương án thay thế
- Source Freshness + Source Conflict Guard
- Weather/Risk/Plan B

## Nguyên tắc
Kinh nghiệm thực chiến là lớp hỗ trợ ra quyết định, không được biến thành dữ kiện lịch sử hay thông tin chính thức. Dữ liệu có nguồn, dữ liệu tham khảo và khoảng trống kiến thức phải được phân biệt.

## QA
- 60 tests passed
- 8 subtests passed
- Release QA kiểm tra version, module bắt buộc, artifact rác và secret pattern.
