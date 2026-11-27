"""HDVIA media warehouse primitives: provenance, rights, quality and verification.

The warehouse stores metadata/manifests rather than copying third-party media by
itself. Binary media should only be persisted when the source/license permits it.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

ROOT = Path(__file__).resolve().parent
MEDIA_INDEX = ROOT / "data" / "warehouse" / "media_index.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def stable_media_id(entity_id: str, url: str) -> str:
    raw = f"{entity_id}\n{url}".encode("utf-8")
    return "media-" + hashlib.sha256(raw).hexdigest()[:20]


def clean_license(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:180]


def build_media_record(*, entity_id: str, entity_name: str, candidate: Dict[str, Any],
                       score: float, confidence: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
    url = str(candidate.get("url") or "").strip()
    return {
        "media_id": stable_media_id(entity_id or entity_name, url),
        "entity_id": entity_id,
        "entity_name": entity_name,
        "media_type": "image",
        "url": url,
        "source": candidate.get("_source") or candidate.get("source") or "unknown",
        "source_url": candidate.get("source_url") or "",
        "title": candidate.get("title") or "",
        "description": candidate.get("description") or "",
        "license": clean_license(candidate.get("license")),
        "artist": candidate.get("artist") or "",
        "score": round(float(score), 1),
        "confidence": confidence,
        "evidence": evidence,
        "verified": confidence == "HIGH",
        "retrieved_at": now(),
        "status": "VERIFIED" if confidence == "HIGH" else "CANDIDATE",
    }


def load_index() -> Dict[str, Any]:
    try:
        return json.loads(MEDIA_INDEX.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"version": "1.0.0", "records": [], "updated_at": None}


def upsert_records(records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    index = load_index()
    existing = {r.get("media_id"): r for r in index.get("records", []) if r.get("media_id")}
    changed = 0
    for record in records:
        mid = record.get("media_id")
        if not mid:
            continue
        existing[mid] = record
        changed += 1
    index["records"] = list(existing.values())[-10000:]
    index["updated_at"] = now()
    MEDIA_INDEX.parent.mkdir(parents=True, exist_ok=True)
    MEDIA_INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"changed": changed, "total": len(index["records"]), "path": str(MEDIA_INDEX)}
