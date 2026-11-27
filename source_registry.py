"""HDVIA source policy registry for the 6-layer data acquisition architecture.

A source can be discoverable without being automatically copyable. Autonomous
collection is allowed only when policy explicitly permits it and the source's
license/terms support the intended use.
"""
from __future__ import annotations

SOURCES = {
    "wikimedia_vi": {
        "id": "wikimedia_vi", "kind": "OPEN_API", "base_url": "https://vi.wikipedia.org/w/api.php",
        "policy": "ALLOWED_AUTO", "license": "CC BY-SA / Wikimedia project terms",
        "attribution": "Wikimedia / Wikipedia contributors", "rate_limit_seconds": 1.0,
        "data_types": ["knowledge", "entity", "image_reference"], "trust": 0.92,
    },
    "wikidata": {
        "id": "wikidata", "kind": "OPEN_API", "base_url": "https://www.wikidata.org/w/api.php",
        "policy": "ALLOWED_AUTO", "license": "CC0", "attribution": "Wikidata / Wikimedia Foundation",
        "rate_limit_seconds": 0.5, "data_types": ["entity", "coordinates", "aliases", "image_reference"], "trust": 0.96,
    },
    "wikimedia_commons": {
        "id": "wikimedia_commons", "kind": "OPEN_MEDIA_API", "base_url": "https://commons.wikimedia.org/w/api.php",
        "policy": "ALLOWED_AUTO", "license": "Per-file Wikimedia Commons license", "attribution": "Wikimedia Commons contributors",
        "rate_limit_seconds": 1.0, "data_types": ["image"], "trust": 0.94,
    },
    "openverse": {
        "id": "openverse", "kind": "OPEN_MEDIA_API", "base_url": "https://api.openverse.org/v1/images/",
        "policy": "ALLOWED_AUTO", "license": "Per-asset license returned by API", "attribution": "Openverse / individual creators",
        "rate_limit_seconds": 0.5, "data_types": ["image"], "trust": 0.90,
    },
    "nominatim_osm": {
        "id": "nominatim_osm", "kind": "OPEN_DATA_API", "base_url": "https://nominatim.openstreetmap.org/search",
        "policy": "ALLOWED_WITH_LIMITS", "license": "ODbL", "attribution": "© OpenStreetMap contributors",
        "rate_limit_seconds": 1.1, "max_requests_per_run": 3, "data_types": ["entity", "coordinates", "poi"], "trust": 0.90,
    },
    "open_data_tourism": {
        "id": "open_data_tourism", "kind": "OFFICIAL_OPEN_DATA", "base_url": "https://dt.gov.vn/applications/tourism",
        "policy": "DISCOVERY_ALLOWED_REVIEW_REQUIRED", "license": "Verify dataset-specific terms before republication",
        "attribution": "Cơ quan cung cấp dữ liệu", "data_types": ["destination", "heritage", "poi", "image_reference"], "trust": 0.98,
    },
    "vietnam_tourism_platform": {
        "id": "vietnam_tourism_platform", "kind": "OFFICIAL_TOURISM", "base_url": "https://nentangso.vietnamtourism.gov.vn",
        "policy": "DISCOVERY_ALLOWED_REVIEW_REQUIRED", "license": "Verify page/dataset reuse terms before republication",
        "attribution": "Cục Du lịch Quốc gia Việt Nam", "data_types": ["destination", "tourism", "image_reference"], "trust": 0.98,
    },
    "khamphadisan": {
        "id": "khamphadisan", "kind": "EDITORIAL_DISCOVERY", "base_url": "https://khamphadisan.com.vn",
        "policy": "MANUAL_REVIEW_ONLY", "license": "Website terms / copyright applies", "attribution": "Khám Phá Di Sản",
        "rate_limit_seconds": 2.0, "max_requests_per_run": 20, "data_types": ["editorial", "image_reference"], "trust": 0.72,
        "ingest_mode": "metadata_and_compact_summary",
    },
    "google_cse": {
        "id": "google_cse", "kind": "OFFICIAL_SEARCH_API", "base_url": "https://www.googleapis.com/customsearch/v1",
        "policy": "ALLOWED_WITH_LIMITS", "license": "Search results only; fetch target page under its own terms",
        "attribution": "Google Custom Search", "data_types": ["discovery"], "trust": 0.65,
    },
}

BLOCKED_AUTO_HOSTS = {"vietravel.com", "saigontourist.net", "vietnam.travel", "booking.com", "agoda.com", "tripadvisor.com"}


def get_source(source_id: str) -> dict:
    if source_id not in SOURCES:
        raise KeyError(f"Unknown source: {source_id}")
    return dict(SOURCES[source_id])


def allowed_for_auto(source_id: str) -> bool:
    return get_source(source_id)["policy"] in {"ALLOWED_AUTO", "ALLOWED_WITH_LIMITS"}


def registry_snapshot() -> dict:
    return {"version": "2.0.0", "sources": SOURCES}
