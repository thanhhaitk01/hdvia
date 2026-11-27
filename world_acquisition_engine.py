"""HDVIA World Data & Media Acquisition Engine.

Seven capabilities built on the existing six-layer pipeline:
1) global source registry/ranking
2) multilingual entity discovery
3) image/media acquisition metadata
4) incremental change detection
5) claim conflict detection
6) provenance/freshness tracking
7) one world-collector orchestration path

The engine is review-safe: external material is never promoted to VERIFIED or
published automatically. Network adapters remain bounded and opt-in.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from typing import Any, Iterable, Mapping

from source_registry import SOURCES, allowed_for_auto

VERSION = "1.30.1-hdv-giau-kinh-nghiem"


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def freshness(observed_at: str, *, now: datetime | None = None, ttl_hours: int = 168) -> str:
    if not observed_at:
        return "UNKNOWN"
    try:
        ts = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
    except ValueError:
        return "UNKNOWN"
    current = now or datetime.now(timezone.utc)
    age = current - ts
    if age < timedelta(hours=ttl_hours):
        return "FRESH"
    if age < timedelta(hours=ttl_hours * 2):
        return "AGING"
    return "STALE"


@dataclass(frozen=True)
class SourceProfile:
    source_id: str
    policy: str
    trust: float
    data_types: tuple[str, ...]
    license: str
    attribution: str


def global_source_catalog() -> list[SourceProfile]:
    return sorted(
        [SourceProfile(k, v.get("policy", "UNKNOWN"), float(v.get("trust", 0)), tuple(v.get("data_types", ())), v.get("license", ""), v.get("attribution", "")) for k, v in SOURCES.items()],
        key=lambda x: (-x.trust, x.source_id),
    )


def discover_sources(kind: str, *, allow_review: bool = True) -> list[dict[str, Any]]:
    result = []
    for p in global_source_catalog():
        if kind not in p.data_types:
            continue
        if not allow_review and not allowed_for_auto(p.source_id):
            continue
        result.append(asdict(p))
    return result


def normalize_alias(value: str) -> str:
    value = value.casefold().strip()
    value = re.sub(r"[’'`´]", "", value)
    value = re.sub(r"[^\w\s-]", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


def multilingual_entity(target: str, aliases: Iterable[str] = (), *, entity_id: str = "") -> dict[str, Any]:
    all_aliases = []
    seen = set()
    for item in [target, *aliases]:
        n = normalize_alias(item)
        if n and n not in seen:
            seen.add(n); all_aliases.append(item.strip())
    return {
        "entity_id": entity_id or "ent:" + digest(all_aliases)[:20],
        "canonical_name": target.strip(),
        "aliases": all_aliases,
        "normalized_aliases": [normalize_alias(x) for x in all_aliases],
        "languages": sorted({"vi" if re.search(r"[à-ỹđ]", x.casefold()) else "und" for x in all_aliases}),
        "status": "CANDIDATE",
    }


def media_asset(*, entity_id: str, url: str, source_id: str, title: str = "", license: str = "", attribution: str = "", source_url: str = "", retrieved_at: str | None = None) -> dict[str, Any]:
    retrieved = retrieved_at or utcnow()
    return {
        "asset_id": "media:" + digest({"entity_id": entity_id, "url": url})[:24],
        "entity_id": entity_id,
        "url": url,
        "source_id": source_id,
        "source_url": source_url,
        "title": title,
        "license": license,
        "attribution": attribution,
        "retrieved_at": retrieved,
        "freshness": freshness(retrieved, ttl_hours=720),
        "usage_status": "REVIEW_REQUIRED" if "Per-file" in license or "Verify" in license else "LICENSE_DECLARED",
        "status": "CANDIDATE",
    }


def diff_record(previous: Mapping[str, Any] | None, current: Mapping[str, Any]) -> dict[str, Any]:
    new_digest = digest(current)
    old_digest = digest(previous) if previous is not None else None
    if previous is None:
        state = "NEW"
    elif old_digest == new_digest:
        state = "UNCHANGED"
    else:
        state = "CHANGED"
    return {"state": state, "previous_digest": old_digest, "current_digest": new_digest, "changed_fields": sorted(set(previous or {}) ^ set(current) | {k for k in current if previous is not None and previous.get(k) != current.get(k)})}


def detect_conflicts(claims: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[Mapping[str, Any]]] = {}
    for claim in claims:
        key = normalize_alias(str(claim.get("subject", ""))) + "|" + normalize_alias(str(claim.get("predicate", "")))
        groups.setdefault(key, []).append(claim)
    conflicts = []
    for key, rows in groups.items():
        values = {json.dumps(r.get("object"), ensure_ascii=False, sort_keys=True) for r in rows}
        if len(values) > 1:
            conflicts.append({"claim_key": key, "status": "CONFLICT", "claims": [dict(r) for r in rows], "resolution": "REVIEW_REQUIRED"})
    return conflicts


class WorldCollector:
    """Review-safe orchestrator. Adapters return candidates; this class only packages them."""

    def __init__(self, *, collector_version: str = VERSION):
        self.collector_version = collector_version

    def package(self, *, target: str, knowledge: Iterable[Mapping[str, Any]] = (), media: Iterable[Mapping[str, Any]] = (), claims: Iterable[Mapping[str, Any]] = ()) -> dict[str, Any]:
        entity = multilingual_entity(target)
        k = []
        for item in knowledge:
            row = dict(item); row.setdefault("status", "CANDIDATE"); row.setdefault("collected_at", utcnow()); row.setdefault("provenance", {}); row["freshness"] = freshness(row["collected_at"]); k.append(row)
        m = [dict(x, status="CANDIDATE") for x in media]
        return {
            "collector_version": self.collector_version,
            "collected_at": utcnow(),
            "target": target,
            "entity": entity,
            "knowledge": k,
            "media": m,
            "conflicts": detect_conflicts(claims),
            "publication_policy": "CANDIDATE_ONLY",
            "ready_for_governance": True,
        }
