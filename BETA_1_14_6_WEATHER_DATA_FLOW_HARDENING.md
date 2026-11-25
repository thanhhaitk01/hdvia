# HDVIA Beta 1.14.6 — Weather Data Flow Hardening

Kế thừa Beta 1.14.5 Open API Orchestrator.

## Sửa luồng thời tiết
- Giữ nguyên ngày thực tế do provider trả về khi normalize dữ liệu.
- Không dùng toàn bộ 7 ngày để cảnh báo cho từng ngày của tour.
- Khi có ngày khởi hành, map Ngày N → đúng ngày lịch tương ứng.
- Khi chưa có ngày khởi hành, map Ngày N → forecast slot N.
- Plan B và Weather Impact dùng đúng dữ liệu thời tiết của ngày đang xét.
- Bổ sung regression tests cho cả hai chế độ mapping.

## Luồng dữ liệu chuẩn
UI Hành Trình → /journey → _ai_query_analyze/_safe_journey_analyze → JourneyIntelligenceEngine → OpenAPIAdapter → Open-Meteo → normalize 7 ngày → day/date mapping → weather_impact/risk/Plan B → template journey.html.
