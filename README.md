# HDVIA Beta 1.14.7 — Open API Orchestrator

Release baseline: `1.14.7-integrated-journey-ai-ui`

Beta 1.14.7 kế thừa Journey/Conversation/Vietnam Knowledge Hardening và bổ sung lớp **Open/Public API Adapter** tách biệt khỏi lõi HDVIA.

## Open/Public providers
- Open-Meteo: weather + geocoding
- OSRM: road routing (opt-in)
- Existing adapters remain available for OSM/Nominatim, Wikipedia, Wikidata, marine, air quality.

## Production safety
- Không hard-code API secrets.
- Timeout có giới hạn.
- Cache TTL cấu hình được.
- Live routing **tắt mặc định** để tránh lạm dụng public OSRM demo server.
- Khi live routing không khả dụng, Journey AI giữ fallback Haversine estimate.

## Environment
See `.env.example` for `HDVIA_OPEN_API_TIMEOUT`, `HDVIA_OPEN_API_CACHE_TTL`, `HDVIA_LIVE_WEATHER`, `HDVIA_LIVE_GEOCODING`, `HDVIA_LIVE_ROUTING`.
