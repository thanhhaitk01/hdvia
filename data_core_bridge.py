"""HDVIA Data Core integration bridge.

The eight warehouses remain the system of record. This layer only resolves
relationships and builds module-ready context; it does not duplicate warehouse data.
"""
from __future__ import annotations
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List
from data_core import COLLECTIONS, ID_FIELDS, resolve_context

class DataCoreBridge:
    VERSION = "2.1.0"

    def __init__(self, db_factory):
        self.db_factory = db_factory

    def load_active(self) -> Dict[str, List[Dict[str, Any]]]:
        c = self.db_factory()
        try:
            return {
                kind: [json.loads(row["payload_json"])
                       for row in c.execute(
                           "SELECT payload_json FROM warehouse_records "
                           "WHERE kind=? AND status IN ('PUBLISHED','ACTIVE') ORDER BY id",
                           (kind,)).fetchall()]
                for kind in COLLECTIONS
            }
        finally:
            c.close()

    @staticmethod
    def _norm(value: str) -> str:
        value = str(value or "").strip().lower()
        value = re.sub(r"[àáạảãâầấậẩẫăằắặẳẵ]", "a", value)
        value = re.sub(r"[èéẹẻẽêềếệểễ]", "e", value)
        value = re.sub(r"[ìíịỉĩ]", "i", value)
        value = re.sub(r"[òóọỏõôồốộổỗơờớợởỡ]", "o", value)
        value = re.sub(r"[ùúụủũưừứựửữ]", "u", value)
        value = re.sub(r"[ỳýỵỷỹ]", "y", value)
        value = value.replace("đ", "d")
        return re.sub(r"[^a-z0-9]+", " ", value).strip()

    def resolve_destination_ids(self, places: Iterable[Dict[str, Any]], records=None) -> List[str]:
        records = records or self.load_active()
        destinations = records.get("destinations", [])
        lookup: Dict[str, str] = {}
        for d in destinations:
            did = d.get("destination_id")
            if not did:
                continue
            for value in [d.get("name"), d.get("slug"), *(d.get("aliases") or [])]:
                key = self._norm(value)
                if key:
                    lookup[key] = did
        ids=[]
        for p in places or []:
            key=self._norm(p.get("name"))
            did=lookup.get(key)
            if did and did not in ids:
                ids.append(did)
        return ids

    def journey_context(self, journey_result: Dict[str, Any]) -> Dict[str, Any]:
        records=self.load_active()
        destination_ids=self.resolve_destination_ids(journey_result.get("places") or [], records)
        # Journey results produced by the engine are runtime objects, not warehouse
        # records. Build a temporary graph anchor so the same resolver is used for
        # both persisted journeys and live Journey Intelligence output.
        if destination_ids:
            graph=resolve_context(records, destination_id=destination_ids[0])
            # Merge all destinations/administrative/linked records for multi-stop trips.
            if len(destination_ids)>1:
                merged={k:list(v) for k,v in graph.items()}
                merged["destinations"]=[]; merged["administrative"]=[]
                merged["knowledge"]=[]; merged["experiences"]=[]; merged["weather_risk"]=[]; merged["market"]=[]; merged["lineage"]=[]
                for did in destination_ids:
                    g=resolve_context(records,destination_id=did)
                    for k in merged:
                        for row in g[k]:
                            rid=row.get(ID_FIELDS[k])
                            if not any(x.get(ID_FIELDS[k])==rid for x in merged[k]):
                                merged[k].append(row)
                graph=merged
        else:
            graph={k:[] for k in COLLECTIONS}
        # Live Journey Intelligence weather is authoritative for the current run.
        # It is merged into the context graph as runtime evidence, not persisted as
        # curated warehouse data. This keeps weather linked without storing stale forecasts.
        live_weather = journey_result.get("weather") or {}
        if isinstance(live_weather, dict):
            for d in graph.get("destinations", []):
                name = d.get("name")
                forecast = live_weather.get(name)
                if not forecast:
                    continue
                rid = f"runtime:{d.get('destination_id')}"
                graph.setdefault("weather_risk", []).append({
                    "risk_id": rid,
                    "destination_id": d.get("destination_id"),
                    "admin_id": d.get("admin_id"),
                    "location_code": d.get("province_code"),
                    "observed_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                    "forecast_type": "LIVE_JOURNEY",
                    "forecast": forecast,
                    "risk_level": (journey_result.get("risk_map") or {}).get(name, {}).get("level", "UNKNOWN"),
                    "source": "Journey Intelligence runtime weather",
                    "status": "RUNTIME"
                })
        return {
            "version": self.VERSION,
            "destination_ids": destination_ids,
            "graph": graph,
            "counts": {k:len(v) for k,v in graph.items()},
        }

    def enrich_journey(self, journey_result: Dict[str, Any]) -> Dict[str, Any]:
        result=dict(journey_result)
        context=self.journey_context(result)
        result["data_core"]={
            "version": context["version"],
            "destination_ids": context["destination_ids"],
            "counts": context["counts"],
            "linked": bool(context["destination_ids"]),
        }
        # Keep full graph available to AI modules without changing the existing
        # Journey UI contract. The graph is additive and read-only.
        result["data_context"]=context["graph"]
        return result
