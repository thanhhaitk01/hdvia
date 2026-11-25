"""HDVIA vendor-neutral open/public data adapter layer.

All providers are optional and fail closed. No API key is stored in source.
Live calls are bounded, cached, and exposed through a single orchestration surface.
"""
from __future__ import annotations
import os, time, json, hashlib
from typing import Any, Dict, Optional
from public_apis import (
    weather as open_meteo_weather, geocode as open_meteo_geocode,
    route as osrm_route, air_quality as open_meteo_air_quality,
    marine as open_meteo_marine, search_place as osm_search_place,
    wikipedia_search, wikidata_search, overpass_query, sun_times,
    opentripmap_places, opentripmap_details,
)

API_LAYER_VERSION = "1.15.0-journey-data-fusion"


def _enabled(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _cache_key(prefix: str, payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return prefix + ":" + hashlib.sha256(raw.encode()).hexdigest()[:24]


class OpenAPIAdapter:
    def __init__(self):
        self.timeout = max(2, min(int(os.getenv("HDVIA_OPEN_API_TIMEOUT", "10")), 30))
        self.live_routing = _enabled("HDVIA_LIVE_ROUTING", False)
        self.live_geocoding = _enabled("HDVIA_LIVE_GEOCODING", True)
        self.live_weather = _enabled("HDVIA_LIVE_WEATHER", True)
        self.live_air_quality = _enabled("HDVIA_LIVE_AIR_QUALITY", True)
        self.live_marine = _enabled("HDVIA_LIVE_MARINE", True)
        self.live_osm = _enabled("HDVIA_LIVE_OSM", True)
        self.live_wikidata = _enabled("HDVIA_LIVE_WIKIDATA", True)
        self.live_wikipedia = _enabled("HDVIA_LIVE_WIKIPEDIA", True)
        self.live_sun = _enabled("HDVIA_LIVE_SUN", True)
        self.live_opentripmap = _enabled("HDVIA_LIVE_OPENTRIPMAP", False)
        self.cache_ttl = max(0, int(os.getenv("HDVIA_OPEN_API_CACHE_TTL", "900")))
        self._cache: Dict[str, tuple[float, Dict[str, Any]]] = {}

    def _cached(self, key: str, fn):
        now = time.time(); hit = self._cache.get(key)
        if hit and (self.cache_ttl == 0 or now - hit[0] < self.cache_ttl):
            out = dict(hit[1]); out["cache"] = "hit"; return out
        try:
            out = fn()
        except Exception as exc:
            out = {"ok": False, "error": str(exc)[:300]}
        if out.get("ok"):
            self._cache[key] = (now, out)
        out = dict(out); out["cache"] = "miss"; return out

    def weather(self, lat: float, lon: float, days: int = 7) -> Dict[str, Any]:
        if not self.live_weather:
            return {"ok": False, "disabled": True, "provider": "open_meteo"}
        return self._cached(_cache_key("weather", [lat, lon, days]), lambda: open_meteo_weather(lat, lon, days))

    def geocode(self, name: str) -> Dict[str, Any]:
        if not self.live_geocoding:
            return {"ok": False, "disabled": True, "provider": "open_meteo_geocoding"}
        return self._cached(_cache_key("geocode", [name]), lambda: open_meteo_geocode(name, 5, "vi"))

    def route(self, coords: str, profile: str = "driving") -> Dict[str, Any]:
        if not self.live_routing:
            return {"ok": False, "disabled": True, "provider": "osrm"}
        return self._cached(_cache_key("route", [coords, profile]), lambda: osrm_route(coords, profile))

    def air_quality(self, lat: float, lon: float) -> Dict[str, Any]:
        if not self.live_air_quality:
            return {"ok": False, "disabled": True, "provider": "open_meteo_air_quality"}
        return self._cached(_cache_key("aqi", [lat, lon]), lambda: open_meteo_air_quality(lat, lon))

    def marine(self, lat: float, lon: float) -> Dict[str, Any]:
        if not self.live_marine:
            return {"ok": False, "disabled": True, "provider": "open_meteo_marine"}
        return self._cached(_cache_key("marine", [lat, lon]), lambda: open_meteo_marine(lat, lon))

    def osm_search(self, q: str, limit: int = 5) -> Dict[str, Any]:
        if not self.live_osm:
            return {"ok": False, "disabled": True, "provider": "osm_nominatim"}
        return self._cached(_cache_key("osm", [q, limit]), lambda: osm_search_place(q, limit))

    def wikidata(self, q: str, limit: int = 5) -> Dict[str, Any]:
        if not self.live_wikidata:
            return {"ok": False, "disabled": True, "provider": "wikidata"}
        return self._cached(_cache_key("wikidata", [q, limit]), lambda: wikidata_search(q, limit))

    def wikipedia(self, q: str, lang: str = "vi", limit: int = 5) -> Dict[str, Any]:
        if not self.live_wikipedia:
            return {"ok": False, "disabled": True, "provider": "wikipedia"}
        return self._cached(_cache_key("wikipedia", [q, lang, limit]), lambda: wikipedia_search(q, lang, limit))

    def overpass(self, query: str) -> Dict[str, Any]:
        if not self.live_osm:
            return {"ok": False, "disabled": True, "provider": "overpass"}
        return self._cached(_cache_key("overpass", query), lambda: overpass_query(query))

    def sun(self, lat: float, lon: float, date: Optional[str] = None) -> Dict[str, Any]:
        if not self.live_sun:
            return {"ok": False, "disabled": True, "provider": "sunrise_sunset"}
        return self._cached(_cache_key("sun", [lat, lon, date]), lambda: sun_times(lat, lon, date))

    def opentripmap_places(self, lat: float, lon: float, radius: int = 5000, kinds: str = "interesting_places") -> Dict[str, Any]:
        if not self.live_opentripmap:
            return {"ok": False, "disabled": True, "provider": "opentripmap"}
        return self._cached(_cache_key("otm_places", [lat, lon, radius, kinds]), lambda: opentripmap_places(lat, lon, radius, kinds))

    def opentripmap_details(self, xid: str) -> Dict[str, Any]:
        if not self.live_opentripmap:
            return {"ok": False, "disabled": True, "provider": "opentripmap"}
        return self._cached(_cache_key("otm_detail", xid), lambda: opentripmap_details(xid))

    def enrich_destination(self, name: str, lat: Optional[float] = None, lon: Optional[float] = None) -> Dict[str, Any]:
        """Read-only enrichment; does not claim external data is verified knowledge."""
        out: Dict[str, Any] = {"ok": True, "query": name, "sources": []}
        if lat is None or lon is None:
            geo = self.geocode(name)
            out["geocode"] = geo
            if geo.get("ok"):
                results = geo.get("data", {}).get("results", [])
                if results:
                    lat = results[0].get("latitude"); lon = results[0].get("longitude")
        if lat is not None and lon is not None:
            out["coordinates"] = {"lat": lat, "lon": lon}
            out["weather"] = self.weather(lat, lon, 7)
            out["air_quality"] = self.air_quality(lat, lon)
            out["sun"] = self.sun(lat, lon)
            out["marine"] = self.marine(lat, lon)
            out["osm"] = self.osm_search(name, 5)
            out["opentripmap"] = self.opentripmap_places(lat, lon, 5000)
        out["wikidata"] = self.wikidata(name, 5)
        out["wikipedia"] = self.wikipedia(name, "vi", 5)
        return out

    def status(self) -> Dict[str, Any]:
        return {"version": API_LAYER_VERSION, "providers": {
            "weather": {"provider":"open_meteo", "enabled": self.live_weather},
            "geocoding": {"provider":"open_meteo_geocoding", "enabled": self.live_geocoding},
            "routing": {"provider":"osrm", "enabled": self.live_routing},
            "air_quality": {"provider":"open_meteo_air_quality", "enabled": self.live_air_quality},
            "marine": {"provider":"open_meteo_marine", "enabled": self.live_marine},
            "osm": {"provider":"osm_nominatim_overpass", "enabled": self.live_osm},
            "wikidata": {"provider":"wikidata", "enabled": self.live_wikidata},
            "wikipedia": {"provider":"wikipedia", "enabled": self.live_wikipedia},
            "sun": {"provider":"sunrise_sunset", "enabled": self.live_sun},
            "opentripmap": {"provider":"opentripmap", "enabled": self.live_opentripmap, "requires_key": True},
        }, "cache_ttl_seconds": self.cache_ttl}


OPEN_API_ADAPTER = OpenAPIAdapter()
