"""HDVIA Knowledge Trust/Quality layer.

Scores provenance, freshness and corroboration without turning retrieved external
content into verified knowledge automatically.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, Iterable

TRUSTED_DOMAIN_HINTS=("gov.vn","unesco.org","who.int","vietnamtourism.gov.vn")


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")


def _age_days(value: Any) -> float | None:
    if not value: return None
    try:
        dt=datetime.fromisoformat(str(value).replace("Z","+00:00"))
        return max(0.0,(datetime.now(timezone.utc)-dt).total_seconds()/86400)
    except Exception:
        return None


def source_score(source: str, source_type: str="") -> float:
    s=str(source or "").lower(); t=str(source_type or "").lower()
    if any(x in s for x in TRUSTED_DOMAIN_HINTS): return .95
    if "wikidata" in s or "wikipedia" in s: return .80
    if "openstreetmap" in s or "nominatim" in s: return .75
    if t in {"manual","guide","official"}: return .90
    return .50


def assess(entry: Dict[str,Any], corroborating_sources: Iterable[str]=()) -> Dict[str,Any]:
    source=str(entry.get("source") or "")
    stype=str(entry.get("source_type") or "")
    base=source_score(source,stype)
    age=_age_days(entry.get("updated_at") or entry.get("collected_at") or entry.get("validated_at"))
    freshness=1.0 if age is None else (1.0 if age<=30 else .9 if age<=180 else .75 if age<=365 else .55)
    corroborated=len({str(x).lower() for x in corroborating_sources if x})
    corroboration=min(.15, corroborated*.05)
    score=min(1.0, round(base*.65+freshness*.25+corroboration,3))
    status="HIGH" if score>=.85 else "MEDIUM" if score>=.65 else "LOW"
    return {"score":score,"status":status,"source_score":base,"freshness_score":round(freshness,3),"corroboration_count":corroborated,"assessed_at":now()}
