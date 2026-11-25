# HDVIA Beta 1.14.8 — Journey Data Fusion

## Mục tiêu
Tích hợp dữ liệu live từ lớp Open API Adapter vào cùng payload của Hành Trình AI, thay vì chỉ hiển thị thời tiết/lộ trình riêng lẻ.

## Luồng
User itinerary → Journey Parser → Destination Resolver → Weather/Routing → Journey Data Fusion → Data Core/Knowledge → Journey Intelligence → Unified Journey UI.

## Provider
- Weather: existing Journey Weather Provider
- Routing: existing route provider
- Geocoding: Open-Meteo Geocoding
- Geography: OpenStreetMap
- Knowledge: Wikipedia + Wikidata
- Air quality: Open-Meteo Air Quality
- Sun: Sunrise-Sunset.org
- Marine: Open-Meteo Marine

## Nguyên tắc
- Provider optional và fail-closed.
- Không coi dữ liệu live là tri thức đã kiểm duyệt nếu không có source.
- Payload fusion bị giới hạn tối đa 4 điểm đến mặc định để bảo vệ thời gian chạy serverless.
- Cache của adapter được tái sử dụng.
- Dữ liệu live là additive; lỗi một provider không làm mất Journey Intelligence.
