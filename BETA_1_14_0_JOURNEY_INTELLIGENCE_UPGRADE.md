# HDVIA Beta 1.14.0 — Journey Intelligence Upgrade

## Mục tiêu
Nâng Hành Trình AI từ parser lịch trình dạng mẫu thành bộ phân tích hiểu hành trình tự nhiên hơn, đồng thời bổ sung time intelligence, weather impact, Plan C và journey memory contract.

## Các giai đoạn đã tích hợp
1. Natural Language Journey Parser: tách `Ngày 1... Ngày 2...` trên cùng dòng, hỗ trợ thứ tự ngày tự nhiên.
2. Journey Model: mỗi ngày có địa điểm, khung thời gian và nhóm hoạt động.
3. Time Intelligence: ước tính thời gian di chuyển và buffer planning. Đây là ước tính planning, không thay thế live routing.
4. Weather Impact: chuyển risk thời tiết thành tác động theo từng ngày.
5. Plan B / Plan C: phương án thay thế theo ngày và phương án fallback khi điều kiện xấu kéo dài.
6. Journey Memory Contract: tạo context_key, summary, days và places để conversation layer có thể dùng làm ngữ cảnh liên tục.

## Regression
Bổ sung `tests/test_journey_intelligence_upgrade.py` cho parser tự nhiên và các trường mới.

## Deploy
Version: `1.14.1-journey-intelligence-hardening`


## Beta 1.14.1 Journey Intelligence Hardening
7. Journey Mutation: hỗ trợ thêm/bỏ/chuyển điểm giữa các ngày từ câu lệnh tự nhiên, có kiểm soát và tái phân tích.
8. Journey Validation: kiểm tra ngày quá dày, ngày rỗng, chặng di chuyển dài, điểm lặp và ngày trùng.
9. Ambiguity Resolver: nhận biết alias địa danh và không tự đoán khi gặp tên địa điểm mơ hồ.
10. Explainable Journey: mỗi cảnh báo/đề xuất quan trọng có bằng chứng và hành động tương ứng.
11. Conversation ↔ Journey: câu lệnh thay đổi hành trình có thể dùng Journey Memory làm context.
