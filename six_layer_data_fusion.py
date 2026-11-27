"""HDVIA 1.25.4 six-layer data fusion contract.

This module is intentionally UI-neutral. It provides one deterministic pipeline
contract from source registry through governed knowledge warehouse output.
External/discovered records can never become VERIFIED solely because retrieval
succeeded.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Iterable
from urllib.parse import urlparse

from source_registry import get_source
from entity_resolution import EntityResolver
from knowledge_quality import assess

VERSION = "1.25.4.4-world-qa-image-rendering"
LAYERS = (
    "source_registry",
    "data_acquisition",
    "entity_resolution",
    "visual_resolution",
    "knowledge_governance",
    "knowledge_warehouse",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def freshness(expires_at: str | None, updated_at: str | None = None) -> str:
    if expires_at:
        try:
            exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if exp <= datetime.now(timezone.utc):
                return "STALE"
        except ValueError:
            return "UNKNOWN"
    if updated_at:
        try:
            age = datetime.now(timezone.utc) - datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            if age <= timedelta(days=30): return "FRESH"
            if age <= timedelta(days=180): return "AGING"
            return "STALE"
        except ValueError:
            return "UNKNOWN"
    return "UNKNOWN"


def _source_meta(source_id: str) -> Dict[str, Any]:
    src = get_source(source_id)
    return {
        "id": src["id"], "kind": src["kind"], "policy": src["policy"],
        "license": src.get("license", ""), "attribution": src.get("attribution", ""),
        "trust": src.get("trust", 0.5),
    }


def governance_status(*, source_id: str, discovered: bool, quality: Dict[str, Any],
                      human_verified: bool = False) -> str:
    policy = get_source(source_id)["policy"]
    if human_verified and quality.get("score", 0) >= 0.65:
        return "VERIFIED"
    if human_verified and policy in {"DISCOVERY_ALLOWED_REVIEW_REQUIRED", "MANUAL_REVIEW_ONLY"}:
        return "VERIFIED"
    if policy in {"DISCOVERY_ALLOWED_REVIEW_REQUIRED", "MANUAL_REVIEW_ONLY"}:
        return "CANDIDATE" if discovered else "REVIEW_REQUIRED"
    return "CANDIDATE"


def build_record(*, source_id: str, payload: Dict[str, Any], entity: Dict[str, Any] | None,
                 media: Dict[str, Any] | None = None, human_verified: bool = False) -> Dict[str, Any]:
    retrieved = payload.get("retrieved_at") or now()
    updated = payload.get("updated_at") or retrieved
    quality_entry = {
        "source": payload.get("source") or source_id,
        "source_type": payload.get("source_type") or _source_meta(source_id)["kind"],
        "updated_at": updated,
    }
    corroborating = payload.get("corroborating_sources") or []
    quality = assess(quality_entry, corroborating)
    record = {
        "fusion_version": VERSION,
        "layer_trace": list(LAYERS),
        "source": _source_meta(source_id),
        "retrieved_at": retrieved,
        "updated_at": updated,
        "expires_at": payload.get("expires_at"),
        "freshness": freshness(payload.get("expires_at"), updated),
        "entity_resolution": entity or {"confidence": "UNRESOLVED"},
        "visual_resolution": media or {"status": "NOT_APPLICABLE"},
        "knowledge_quality": quality,
        "status": governance_status(source_id=source_id, discovered=True, quality=quality, human_verified=human_verified),
        "data": {k: v for k, v in payload.items() if k not in {"source", "source_type", "retrieved_at", "updated_at", "expires_at", "corroborating_sources"}},
    }
    return record


def resolve_and_fuse(name: str, adapter: Any, *, source_id: str = "wikidata",
                     wikipedia_vi: Dict[str, Any] | None = None,
                     wikipedia_en: Dict[str, Any] | None = None,
                     wikidata_direct: Dict[str, Any] | None = None,
                     media: Dict[str, Any] | None = None) -> Dict[str, Any]:
    entity = EntityResolver(adapter).resolve(name, wikipedia_vi=wikipedia_vi,
                                              wikipedia_en=wikipedia_en,
                                              wikidata_direct=wikidata_direct)
    payload = {"name": name, "source": source_id, "source_type": "OPEN_API", "retrieved_at": now()}
    return build_record(source_id=source_id, payload=payload, entity=entity, media=media)


def layer_health() -> Dict[str, Any]:
    return {"version": VERSION, "layers": list(LAYERS), "count": len(LAYERS), "status": "PASS"}
