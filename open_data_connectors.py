"""Provider-neutral open-data connectors for HDVIA.

No API key is required for the included prototype connectors. External data is
returned with attribution/source metadata and can be fed into the existing
CANDIDATE-only ingestion pipeline. The public Nominatim service is intentionally
rate-limited and is not used for autocomplete or bulk harvesting.
"""
from __future__ import annotations
import json, os, time, urllib.parse, urllib.request, urllib.error
from typing import Any, Dict, List, Optional

from data_acquisition import USER_AGENT

NOMINATIM_URL = os.environ.get("HDVIA_NOMINATIM_URL", "https://nominatim.openstreetmap.org/search")
GEONAMES_URL = os.environ.get("HDVIA_GEONAMES_URL", "http://api.geonames.org/searchJSON")
NOMINATIM_MIN_INTERVAL = float(os.environ.get("HDVIA_NOMINATIM_MIN_INTERVAL", "1.05"))
_last_nominatim_call = 0.0


def _get_json(url: str, *, headers: Optional[Dict[str, str]] = None, timeout: int = 15) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode(resp.headers.get_content_charset() or "utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        raise ValueError(f"Nguồn dữ liệu mở trả HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"Không truy cập được nguồn dữ liệu mở: {exc.reason}") from exc


def osm_nominatim_search(query: str, *, limit: int = 5, countrycodes: str = "vn") -> Dict[str, Any]:
    """End-user-triggered OSM place lookup, deliberately rate limited."""
    global _last_nominatim_call
    q = str(query or "").strip()
    if not q:
        raise ValueError("Thiếu truy vấn địa điểm")
    now = time.monotonic()
    wait = NOMINATIM_MIN_INTERVAL - (now - _last_nominatim_call)
    if wait > 0:
        time.sleep(wait)
    params = urllib.parse.urlencode({"q": q, "format": "jsonv2", "limit": max(1, min(10, int(limit))), "addressdetails": "1", "countrycodes": countrycodes})
    data = _get_json(f"{NOMINATIM_URL}?{params}", headers={"Accept-Language": "vi,en"})
    _last_nominatim_call = time.monotonic()
    results = []
    for x in data if isinstance(data, list) else []:
        results.append({
            "osm_type": x.get("osm_type"), "osm_id": x.get("osm_id"),
            "name": x.get("name") or x.get("display_name", "").split(",")[0],
            "display_name": x.get("display_name", ""), "lat": x.get("lat"), "lon": x.get("lon"),
            "type": x.get("type"), "category": x.get("category"), "address": x.get("address", {}),
            "source": "OpenStreetMap/Nominatim"
        })
    return {"provider": "osm_nominatim", "query": q, "results": results,
            "attribution": "© OpenStreetMap contributors", "policy": "end_user_lookup_rate_limited"}


def geonames_search(query: str, *, username: str = "", max_rows: int = 5, country: str = "VN") -> Dict[str, Any]:
    """GeoNames lookup. A free GeoNames account username is required by its web service."""
    q = str(query or "").strip()
    user = (username or os.environ.get("GEONAMES_USERNAME", "")).strip()
    if not q:
        raise ValueError("Thiếu truy vấn địa danh")
    if not user:
        raise ValueError("Thiếu GEONAMES_USERNAME; dữ liệu GeoNames vẫn có thể dùng bằng file tải về")
    params = urllib.parse.urlencode({"q": q, "maxRows": max(1, min(10, int(max_rows))), "country": country, "lang": "vi", "username": user, "style": "MEDIUM"})
    data = _get_json(f"{GEONAMES_URL}?{params}")
    results = []
    for x in data.get("geonames", []):
        results.append({"geoname_id": x.get("geonameId"), "name": x.get("name"), "ascii_name": x.get("asciiName"),
                        "lat": x.get("lat"), "lng": x.get("lng"), "feature_class": x.get("fcl"),
                        "feature_code": x.get("fcode"), "country_code": x.get("countryCode"),
                        "admin_name1": x.get("adminName1"), "population": x.get("population"),
                        "source": "GeoNames"})
    return {"provider": "geonames", "query": q, "results": results, "attribution": "GeoNames"}


def open_data_status() -> Dict[str, Any]:
    return {"providers": {
        "osm_nominatim": {"enabled": True, "api_key_required": False, "mode": "end_user_lookup", "rate_limit": ">=1.05s between requests"},
        "geonames": {"enabled": bool(os.environ.get("GEONAMES_USERNAME")), "api_key_required": False, "account_username_required": True, "mode": "web_service"},
        "geonames_download": {"enabled": True, "api_key_required": False, "mode": "daily_open_data"},
    }, "policy": "open-data-first; attribution required; external results remain candidates until validation/review/publish"}
