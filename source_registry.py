"""HDVIA source policy registry for open/free acquisition.

Only sources explicitly marked ALLOWED_AUTO are eligible for autonomous collection.
Restricted/commercial sites are intentionally excluded from the agent.
"""
from __future__ import annotations

SOURCES = {
    "wikimedia_vi": {
        "id": "wikimedia_vi",
        "kind": "OPEN_API",
        "base_url": "https://vi.wikipedia.org/w/api.php",
        "policy": "ALLOWED_AUTO",
        "license": "CC BY-SA / project-specific Wikimedia terms",
        "attribution": "Wikimedia / Wikipedia contributors",
        "rate_limit_seconds": 1.0,
    },
    "nominatim_osm": {
        "id": "nominatim_osm",
        "kind": "OPEN_DATA_API",
        "base_url": "https://nominatim.openstreetmap.org/search",
        "policy": "ALLOWED_WITH_LIMITS",
        "license": "ODbL",
        "attribution": "© OpenStreetMap contributors",
        "rate_limit_seconds": 1.1,
        "max_requests_per_run": 3,
    },
    "khamphadisan": {
        "id": "khamphadisan",
        "kind": "EDITORIAL_DISCOVERY",
        "base_url": "https://khamphadisan.com.vn",
        "policy": "MANUAL_REVIEW_ONLY",
        "license": "Website terms / copyright applies",
        "attribution": "Khám Phá Di Sản",
        "rate_limit_seconds": 2.0,
        "max_requests_per_run": 20,
        "ingest_mode": "metadata_and_compact_summary",
        "note": "Không tự động sao chép toàn văn bài viết; chỉ lưu metadata/tóm tắt ngắn và liên kết nguồn để kiểm chứng."
    },
}

BLOCKED_AUTO_HOSTS = {
    "vietravel.com",
    "saigontourist.net",
    "vietnam.travel",
}


def get_source(source_id: str) -> dict:
    if source_id not in SOURCES:
        raise KeyError(f"Unknown source: {source_id}")
    return dict(SOURCES[source_id])


def allowed_for_auto(source_id: str) -> bool:
    return get_source(source_id)["policy"] in {"ALLOWED_AUTO", "ALLOWED_WITH_LIMITS"}
