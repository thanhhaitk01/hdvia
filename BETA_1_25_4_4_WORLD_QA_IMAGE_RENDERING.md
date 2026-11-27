# HDVIA Beta 1.25.4.4 — World QA + Image Rendering Hardened

## Mục tiêu
Sửa dứt điểm đường hiển thị ảnh đại diện điểm đến và tăng cường QA giao tiếp Hành Trình AI.

## Thay đổi chính
- Destination cards render `image_url` thực tế từ media metadata.
- Destination detail render ảnh đại diện + source/license/artist metadata.
- Giữ fallback Verified Image Resolver trong Hành Trình AI khi ảnh curated lỗi hoặc thiếu.
- Bổ sung regression contract cho destination image rendering.
- Chuẩn hóa runtime/release version `1.25.4.4-world-qa-image-rendering`.
- Giữ nguyên các module và kiến trúc 6 Layer Data Fusion / World Data Acquisition.

## QA
- 39 tests PASS + 8 subtests PASS.
- 1,200,000 routing/entity QA cases đã chạy: 12 chủ đề × 100,000 biến thể, 0 sai intent, 0 mất place resolution.
- 12,000 full-answer samples đã chạy: 12 chủ đề × 1,000 câu, 0 exception, 0 mất place resolution.
- Bộ harness `stress_world_qa.py` hỗ trợ chạy 1,000,000 cases/chủ đề khi chạy trong môi trường QA mở rộng. Full 12 triệu full-answer cases không được coi là đã hoàn thành chỉ từ vòng kiểm thử hiện tại.
- Kiểm tra image metadata contract cho 8 điểm curated: PASS.

## Giới hạn QA
Không thể xác nhận HTTP tải ảnh Wikimedia trực tiếp trong môi trường sandbox hiện tại vì môi trường không phân giải được `commons.wikimedia.org`. Điều này không được coi là lỗi của URL trong release; cần browser/deployed environment để xác nhận tải ảnh end-to-end.
