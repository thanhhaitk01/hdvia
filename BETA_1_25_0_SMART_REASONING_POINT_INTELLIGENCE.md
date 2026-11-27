# HDVIA BETA 1.25.0 – HDV Smart Reasoning & Point Intelligence

## Mục tiêu
Nâng cấp HDVIA từ truy xuất theo từ khóa sang truy xuất có ngữ cảnh, ưu tiên đúng yêu cầu của HDV, giữ đủ các địa điểm trong câu hỏi và phân biệt rõ tri thức đã kiểm duyệt với nguồn tham khảo/khám phá.

## Những gì được nâng cấp
- Intent-aware multi-signal retrieval trong Kho tri thức.
- Query Contract: xác định yêu cầu chính, các chiều thông tin cần trả lời, số ngày và toàn bộ địa điểm được nhắc tới.
- Giữ nguyên multi-location context; không tự bỏ địa điểm thứ hai/thứ ba.
- Source classification: CURATED_CATALOG / VERIFIED_SOURCE / EDITORIAL_REFERENCE / DISCOVERY.
- Không gắn dữ liệu Khám Phá Di Sản thành dữ liệu đã xác minh.
- Tăng điểm ưu tiên cho catalog chính thống nội bộ, exact phrase, địa điểm và chủ đề phù hợp.
- Giữ nguyên giao diện và module hiện có; không thêm module UI.
- Giữ nguyên cơ chế live weather/routing/fusion của 1.24.
- Giữ nguyên nguyên tắc không bịa chi tiết khi thiếu nguồn.

## Phạm vi dữ liệu
- 34 tỉnh/thành cấp tỉnh.
- 3.321 đơn vị cấp xã ở trạng thái registry/reference theo manifest; chưa tuyên bố đã nạp đầy đủ hồ sơ chi tiết cho 3.321 đơn vị.
- Điểm đến, di sản, ẩm thực, trải nghiệm, guide script và check-in discovery.
- Khám Phá Di Sản: chỉ dùng metadata/tóm tắt có cấu trúc, không sao chép toàn văn.

## Kiểm thử
- 181/181 tests PASS.
- Regression của 1.24 được giữ lại.
- Có thêm test cho query contract, multi-location preservation, intent-aware retrieval và source labeling.

## Quy tắc chất lượng
Live data và editorial reference không tự động trở thành verified fact. Khi thiếu nguồn phù hợp, HDVIA phải nói rõ giới hạn dữ liệu thay vì suy đoán.
