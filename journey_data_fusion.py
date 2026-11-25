"""Journey Data Fusion for HDVIA 1.22.0.

Turns the existing vendor-neutral API adapters into a single, small, reviewable
payload consumed by Journey AI. External providers are optional and fail closed;
no provider response is treated as curated knowledge without a source label.
"""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

from api_adapters import OPEN_API_ADAPTER
from knowledge_intelligence import destination_card


FUSION_VERSION = "1.22.0-journey-data-fusion"


def _enabled(name: str, default: bool = True) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _first(mapping: Any, *paths: str) -> Any:
    if not isinstance(mapping, dict):
        return None
    for path in paths:
        value: Any = mapping
        for key in path.split("."):
            if not isinstance(value, dict):
                value = None
                break
            value = value.get(key)
        if value is not None:
            return value
    return None


class JourneyDataFusion:
    """Build a bounded live-data package for each recognized journey place."""

    def __init__(self, adapter=None):
        self.adapter = adapter or OPEN_API_ADAPTER
        self.max_places = max(1, min(int(os.getenv("HDVIA_JOURNEY_FUSION_MAX_PLACES", "4")), 8))
        self.enabled = _enabled("HDVIA_JOURNEY_LIVE_FUSION", True)

    def _provider(self, name: str, fn) -> Dict[str, Any]:
        try:
            result = fn()
            if not isinstance(result, dict):
                return {"ok": False, "provider": name, "error": "invalid_response"}
            result.setdefault("provider", name)
            return result
        except Exception as exc:
            return {"ok": False, "provider": name, "error": str(exc)[:180]}

    @staticmethod
    def _aqi_summary(result: Dict[str, Any]) -> Dict[str, Any]:
        data = result.get("data") if isinstance(result, dict) else {}
        hourly = data.get("hourly", {}) if isinstance(data, dict) else {}
        times = hourly.get("time") or []
        for key in ("european_aqi", "pm2_5", "pm10"):
            values = hourly.get(key) or []
            if values:
                value = values[0]
                return {"metric": key, "value": value, "time": times[0] if times else None}
        return {}

    @staticmethod
    def _sun_summary(result: Dict[str, Any]) -> Dict[str, Any]:
        data = result.get("data") if isinstance(result, dict) else {}
        return {
            "sunrise": data.get("sunrise"),
            "sunset": data.get("sunset"),
            "civil_twilight_begin": data.get("civil_twilight_begin"),
            "civil_twilight_end": data.get("civil_twilight_end"),
        }

    @staticmethod
    def _marine_summary(result: Dict[str, Any]) -> Dict[str, Any]:
        data = result.get("data") if isinstance(result, dict) else {}
        hourly = data.get("hourly", {}) if isinstance(data, dict) else {}
        times = hourly.get("time") or []
        out = {}
        for key in ("wave_height", "wave_direction", "wave_period"):
            values = hourly.get(key) or []
            if values:
                out[key] = values[0]
        if times:
            out["time"] = times[0]
        return out

    @staticmethod
    def _search_summary(result: Dict[str, Any], limit: int = 3) -> list[Dict[str, Any]]:
        data = result.get("data") if isinstance(result, dict) else {}
        if not isinstance(data, dict):
            return []
        rows = data.get("results") or data.get("search") or data.get("data") or []
        if not isinstance(rows, list):
            return []
        out=[]
        for row in rows[:limit]:
            if not isinstance(row, dict):
                continue
            item={}
            for key in ("name", "display_name", "title", "description", "snippet", "summary", "type", "lat", "lon", "wikibase_item", "pageid", "xid"):
                if row.get(key) is not None:
                    item[key]=row[key]
            if item:
                out.append(item)
        return out

    def _place(self, place: Dict[str, Any], existing_weather: Optional[list] = None) -> Dict[str, Any]:
        name=str(place.get("name") or "").strip()
        lat=place.get("lat"); lon=place.get("lon")
        sources=[]
        provider_status={}

        if lat is None or lon is None:
            geo=self._provider("open_meteo_geocoding", lambda: self.adapter.geocode(name))
            provider_status["geocoding"]={"ok":bool(geo.get("ok")),"provider":geo.get("provider","open_meteo_geocoding")}
            results=_first(geo,"data.results") or []
            if geo.get("ok") and results:
                lat=results[0].get("latitude"); lon=results[0].get("longitude")
                if lat is not None and lon is not None:
                    sources.append("Open-Meteo Geocoding")

        out: Dict[str, Any] = {
            "name": name,
            "coordinates": {"lat": lat, "lon": lon} if lat is not None and lon is not None else None,
            "weather": {"forecast": (existing_weather or [])[:7], "source": "Journey Weather Provider"} if existing_weather else None,
            "providers": provider_status,
            "sources": sources,
        }

        if lat is None or lon is None:
            out["availability"]="PARTIAL"
            out["note"]="Chưa có tọa độ đủ tin cậy để gọi dữ liệu địa lý trực tiếp."
            return out

        calls={
            "air_quality": lambda: self.adapter.air_quality(float(lat), float(lon)),
            "sun": lambda: self.adapter.sun(float(lat), float(lon)),
            "marine": lambda: self.adapter.marine(float(lat), float(lon)),
            "osm": lambda: self.adapter.osm_search(name, 5),
            "wikipedia": lambda: self.adapter.wikipedia(name, "vi", 5),
            "wikidata": lambda: self.adapter.wikidata(name, 5),
        }
        results: Dict[str, Dict[str, Any]]={}
        with ThreadPoolExecutor(max_workers=min(6, len(calls))) as pool:
            futures={pool.submit(self._provider, key, fn):key for key,fn in calls.items()}
            for future in as_completed(futures):
                key=futures[future]
                try:
                    results[key]=future.result()
                except Exception as exc:
                    results[key]={"ok":False,"provider":key,"error":str(exc)[:180]}

        for key,result in results.items():
            provider_status[key]={"ok":bool(result.get("ok")),"provider":result.get("provider",key),"cache":result.get("cache")}
            if result.get("ok"):
                label={"air_quality":"Open-Meteo Air Quality","sun":"Sunrise-Sunset.org","marine":"Open-Meteo Marine","osm":"OpenStreetMap","wikipedia":"Wikipedia","wikidata":"Wikidata"}.get(key,key)
                sources.append(label)

        out["air_quality"]={"summary":self._aqi_summary(results.get("air_quality",{})),"raw_status":provider_status.get("air_quality")}
        out["sun"]={"summary":self._sun_summary(results.get("sun",{})),"raw_status":provider_status.get("sun")}
        out["marine"]={"summary":self._marine_summary(results.get("marine",{})),"raw_status":provider_status.get("marine")}
        out["osm"]={"results":self._search_summary(results.get("osm",{})),"raw_status":provider_status.get("osm")}
        out["wikipedia"]={"results":self._search_summary(results.get("wikipedia",{})),"raw_status":provider_status.get("wikipedia")}
        out["wikidata"]={"results":self._search_summary(results.get("wikidata",{})),"raw_status":provider_status.get("wikidata")}
        out["availability"]="LIVE_PARTIAL" if sources else "CURATED_ONLY"
        out["sources"] = list(dict.fromkeys(sources))
        profile=str(os.getenv("HDVIA_TOURIST_PROFILE", "general")).strip().lower()
        out["knowledge_card"] = destination_card(name, live=out, tourist_profile=profile)
        return out

    def enrich_result(self, journey_result: Dict[str, Any]) -> Dict[str, Any]:
        result=dict(journey_result or {})
        places=list(result.get("places") or [])[:self.max_places]
        if not self.enabled or not places:
            result["live_data_fusion"]={"version":FUSION_VERSION,"enabled":False,"destinations":{},"providers":{}}
            return result

        weather=result.get("weather") if isinstance(result.get("weather"),dict) else {}
        destinations={}
        with ThreadPoolExecutor(max_workers=min(4,len(places))) as pool:
            futures={pool.submit(self._place,p,weather.get(p.get("name"),[])):p for p in places}
            for future in as_completed(futures):
                p=futures[future]
                name=p.get("name")
                try:
                    destinations[name]=future.result()
                except Exception as exc:
                    destinations[name]={"name":name,"availability":"ERROR","error":str(exc)[:180],"sources":[]}

        # Seven-part Journey Data Fusion: four knowledge layers + three safe data systems.
        days=[]
        for day in result.get("days") or []:
            day_places=day.get("places") or []
            cards=[]
            for p in day_places:
                name=p.get("name") if isinstance(p,dict) else str(p)
                live=destinations.get(name,{})
                profile=str(os.getenv("HDVIA_TOURIST_PROFILE", "general")).strip().lower()
                cards.append(live.get("knowledge_card") or destination_card(name, live=live, tourist_profile=profile))
            days.append({"day":day.get("day"),"text":day.get("text"),"places":[p.get("name") if isinstance(p,dict) else str(p) for p in day_places],"knowledge":cards})
        result["journey_data_package"]={"version":"1.0.0","layers":list(("geography","culture_history","tourism","nature_operations")),"systems":{"destination_schema":True,"world_acquisition":"CANDIDATE_ONLY","fusion_confidence":True,"knowledge_quality":True,"knowledge_graph":True,"external_verification":"CANDIDATE_ONLY"},"days":days}
        result["live_data_fusion"]={
            "version":FUSION_VERSION,
            "enabled":True,
            "generated_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
            "max_places":self.max_places,
            "destinations":destinations,
            "providers":{
                "weather":"Journey Weather Provider", "routing":"Journey Route Provider",
                "knowledge":"Wikipedia + Wikidata", "geography":"OpenStreetMap",
                "air_quality":"Open-Meteo Air Quality", "sun":"Sunrise-Sunset.org", "marine":"Open-Meteo Marine",
            },
        }
        return result


JOURNEY_DATA_FUSION = JourneyDataFusion()
