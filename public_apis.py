"""Free/public travel-data providers for HDVIA.

Providers are read-only and use official/public HTTP endpoints. They are exposed
through one normalized adapter surface so Journey/Conversation layers can call
external data without coupling themselves to a vendor.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional


class PublicAPIError(Exception):
    pass


@dataclass(frozen=True)
class PublicProvider:
    name: str
    base_url: str
    attribution: str
    rate_limit_note: str = ""

    def get(self, path: str = "", params: Optional[Mapping[str, Any]] = None, *, timeout: int = 12) -> Dict[str, Any]:
        base = self.base_url.rstrip("/") + "/" + path.lstrip("/")
        query = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v is not None}, doseq=True)
        url = base + ("?" + query if query else "")
        req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": os.getenv("HDVIA_API_USER_AGENT", "HDVIA-PublicAPI/1.15.0")})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read(2_000_001)
                if len(raw) > 2_000_000:
                    raise PublicAPIError("Public API response vượt 2 MB")
                text = raw.decode(resp.headers.get_content_charset() or "utf-8", errors="replace")
                try:
                    data = json.loads(text) if text else {}
                except json.JSONDecodeError:
                    data = {"text": text[:12000]}
                return {"ok": True, "provider": self.name, "status_code": getattr(resp, "status", 200), "data": data,
                        "attribution": self.attribution}
        except Exception as exc:
            return {"ok": False, "provider": self.name, "error": str(exc)[:300], "attribution": self.attribution}


PROVIDERS = {
    "open_meteo": PublicProvider("open_meteo", "https://api.open-meteo.com", "Open-Meteo / CC BY 4.0"),
    "open_meteo_geocoding": PublicProvider("open_meteo_geocoding", "https://geocoding-api.open-meteo.com", "Open-Meteo / CC BY 4.0"),
    "open_meteo_air_quality": PublicProvider("open_meteo_air_quality", "https://air-quality-api.open-meteo.com", "Open-Meteo / CC BY 4.0"),
    "open_meteo_marine": PublicProvider("open_meteo_marine", "https://marine-api.open-meteo.com", "Open-Meteo / CC BY 4.0"),
    "osm_nominatim": PublicProvider("osm_nominatim", "https://nominatim.openstreetmap.org", "© OpenStreetMap contributors", "Public server: max 1 request/second; identify User-Agent."),
    "osrm": PublicProvider("osrm", "https://router.project-osrm.org", "© OpenStreetMap contributors", "Public demo server; cache and rate-limit production traffic."),
    "wikipedia": PublicProvider("wikipedia", "https://en.wikipedia.org", "Wikipedia / Wikimedia Foundation"),
    "wikidata": PublicProvider("wikidata", "https://www.wikidata.org", "Wikidata / Wikimedia Foundation"),
    "rest_countries": PublicProvider("rest_countries", "https://api.restcountries.com", "REST Countries"),
}


def weather(lat: float, lon: float, days: int = 7) -> Dict[str, Any]:
    return PROVIDERS["open_meteo"].get("/v1/forecast", {
        "latitude": lat, "longitude": lon, "forecast_days": min(max(int(days), 1), 16),
        "timezone": "auto", "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max"
    })


def geocode(name: str, count: int = 5, language: str = "vi") -> Dict[str, Any]:
    return PROVIDERS["open_meteo_geocoding"].get("/v1/search", {"name": name, "count": min(max(int(count), 1), 10), "language": language, "format": "json"})


def air_quality(lat: float, lon: float) -> Dict[str, Any]:
    return PROVIDERS["open_meteo_air_quality"].get("/v1/air-quality", {"latitude": lat, "longitude": lon, "hourly": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,ozone,european_aqi", "timezone": "auto"})


def marine(lat: float, lon: float) -> Dict[str, Any]:
    return PROVIDERS["open_meteo_marine"].get("/v1/marine", {"latitude": lat, "longitude": lon, "hourly": "wave_height,wave_direction,wave_period", "timezone": "auto"})


def search_place(q: str, limit: int = 5) -> Dict[str, Any]:
    return PROVIDERS["osm_nominatim"].get("/search", {"q": q, "format": "jsonv2", "limit": min(max(int(limit), 1), 10), "addressdetails": 1})


def route(coords: str, profile: str = "driving") -> Dict[str, Any]:
    # coords format: lon,lat;lon,lat
    return PROVIDERS["osrm"].get(f"/route/v1/{profile}/{coords}", {"overview": "false", "steps": "false"})


def wikipedia_search(q: str, lang: str = "en", limit: int = 5) -> Dict[str, Any]:
    p = PublicProvider("wikipedia", f"https://{lang}.wikipedia.org", "Wikipedia / Wikimedia Foundation")
    return p.get("/w/api.php", {"action": "query", "list": "search", "srsearch": q, "srlimit": min(max(int(limit), 1), 10), "format": "json", "origin": "*"})


def wikidata_search(q: str, limit: int = 5) -> Dict[str, Any]:
    return PROVIDERS["wikidata"].get("/w/api.php", {"action": "wbsearchentities", "search": q, "language": "en", "format": "json", "limit": min(max(int(limit), 1), 10), "origin": "*"})


def country(name_or_code: str) -> Dict[str, Any]:
    # REST Countries v5 currently requires a bearer token for API calls. The
    # public demo key is intentionally not baked into HDVIA; deployment can set it.
    return PROVIDERS["rest_countries"].get(f"/countries/v5/name/{urllib.parse.quote(name_or_code)}", {"pretty": "0"})


def overpass_query(query: str) -> Dict[str, Any]:
    return PROVIDERS["osm_nominatim"].get("https://overpass-api.de/api/interpreter" if False else "", {}) if False else _raw_post_json("https://overpass-api.de/api/interpreter", query, "overpass")


def sun_times(lat: float, lon: float, date: Optional[str] = None) -> Dict[str, Any]:
    return PublicProvider("sunrise_sunset", "https://api.sunrise-sunset.org", "Sunrise-Sunset.org").get("/json", {"lat": lat, "lng": lon, "date": date or "today", "formatted": 0})


def opentripmap_places(lat: float, lon: float, radius: int = 5000, kinds: str = "interesting_places") -> Dict[str, Any]:
    key = os.getenv("OPENTRIPMAP_API_KEY", "")
    if not key:
        return {"ok": False, "provider": "opentripmap", "disabled": True, "error": "OPENTRIPMAP_API_KEY not configured"}
    return PublicProvider("opentripmap", "https://api.opentripmap.com", "OpenTripMap / ODbL").get("/0.1/en/places/radius", {"radius": min(max(int(radius), 100), 50000), "lon": lon, "lat": lat, "kinds": kinds, "format": "json", "apikey": key})


def opentripmap_details(xid: str) -> Dict[str, Any]:
    key = os.getenv("OPENTRIPMAP_API_KEY", "")
    if not key:
        return {"ok": False, "provider": "opentripmap", "disabled": True, "error": "OPENTRIPMAP_API_KEY not configured"}
    return PublicProvider("opentripmap", "https://api.opentripmap.com", "OpenTripMap / ODbL").get(f"/0.1/en/places/xid/{urllib.parse.quote(xid)}", {"apikey": key})


def _raw_post_json(url: str, body: str, provider: str) -> Dict[str, Any]:
    encoded = urllib.parse.urlencode({"data": body}).encode("utf-8")
    req = urllib.request.Request(url, data=encoded, headers={"Accept":"application/json", "Content-Type":"application/x-www-form-urlencoded", "User-Agent": os.getenv("HDVIA_API_USER_AGENT", "HDVIA-PublicAPI/1.15.0")}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            raw = resp.read(2_000_001)
            if len(raw) > 2_000_000:
                raise PublicAPIError("Public API response vượt 2 MB")
            return {"ok": True, "provider": provider, "status_code": getattr(resp, "status", 200), "data": json.loads(raw.decode("utf-8", errors="replace")), "attribution":"© OpenStreetMap contributors"}
    except Exception as exc:
        return {"ok": False, "provider": provider, "error": str(exc)[:300], "attribution":"© OpenStreetMap contributors"}
