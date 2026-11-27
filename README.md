# HDVIA Beta 1.22.0 — Journey Data Fusion

Release baseline: `1.22.0-tour-intelligence`

Beta 1.22.0 kế thừa Journey/Conversation/Vietnam Knowledge Hardening và bổ sung lớp **Open/Public API Adapter** tách biệt khỏi lõi HDVIA.

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
See `.env.example` for `HDVIA_OPEN_API_TIMEOUT`, `HDVIA_OPEN_API_CACHE_TTL`, `HDVIA_LIVE_WEATHER`, `HDVIA_LIVE_GEOCODING`, `HDVIA_LIVE_ROUTING`. For routing, `HDVIA_ENABLE_LIVE_ROUTING=true` can override the legacy `HDVIA_LIVE_ROUTING` flag without changing existing deployments.

## Beta 1.22.0 Knowledge Expansion

HDVIA 1.14.8 includes a controlled Knowledge Expansion Engine on top of Journey Data Fusion. It provides:
- 9 knowledge domains: geography, history, culture, people, food, tourism, nature, operations, guide experience.
- Destination coverage scoring and explicit knowledge-gap detection.
- A lightweight destination knowledge graph derived from curated entries.
- Tourist-profile-aware ranking for general, India, Korea and Europe profiles; profiles change presentation priority, not verified facts.
- HDV contribution intake as `CANDIDATE` only; provenance and validation remain required before publication.
- Existing live providers and 7-layer Journey Data Fusion remain intact.

External data is never treated as verified merely because it was retrieved successfully.


## Beta 1.22.0 — Knowledge & Journey Intelligence Upgrade

This release keeps the 1.14.8 seven-layer Data Fusion baseline and adds five hardening layers:
- Knowledge Graph 1.1.0 with explicit verified/external edges.
- Knowledge Quality/Trust scoring with provenance and freshness signals.
- Journey Feasibility output with live routing when enabled and explicit estimate/traffic limitations.
- Explainable Decision Trace linking recommendations to deterministic evidence.
- Expanded Knowledge Expansion integration without auto-publishing external or HDV contributions.

External data remains `CANDIDATE_ONLY` until the validation pipeline promotes it.
