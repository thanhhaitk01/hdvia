# HDVIA Beta 1.14.5 — Open API Orchestrator

Adds vendor-neutral orchestration for open/public travel data: weather, geocoding, routing, air quality, marine conditions, OSM/Nominatim/Overpass, Wikidata, Wikipedia, sunrise/sunset, and optional OpenTripMap.

All external providers are optional, bounded, cached, and fail closed. API keys are supplied only through environment variables. External data is never automatically promoted to verified HDVIA knowledge.

Release baseline: `1.14.5-open-api-orchestrator`.


## Pre-deploy checklist
- Configure `HDVIA_SECRET_KEY`, `HDVIA_ADMIN_EMAIL`, and `HDVIA_DEMO_ADMIN_PASSWORD` in deployment environment; none are bundled in source.
- Keep `HDVIA_LIVE_ROUTING=0` unless a production routing provider and rate-limit policy are configured.
- Set a descriptive `HDVIA_API_USER_AGENT` for public OSM/Nominatim access.
- Open/public API failures are non-fatal: Journey AI falls back to cached/HDVIA estimates where supported.
- Run `PYTHONPATH=. pytest -q --ignore=tests/stress_100m_vietnam.py --ignore=tests/stress_100m_worker.py` before release.
