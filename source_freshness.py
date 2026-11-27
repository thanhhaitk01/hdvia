"""Evidence freshness and temporal guardrails for HDVIA 1.30.1."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List

def normalize_evidence(items: Iterable[Dict[str, Any]] | None) -> List[Dict[str, Any]]:
    out=[]
    for x in items or []:
        if not isinstance(x, dict): continue
        out.append({"source": x.get("source") or x.get("url") or "UNKNOWN", "published_at": x.get("published_at"),
                    "updated_at": x.get("updated_at"), "valid_from": x.get("valid_from"), "valid_to": x.get("valid_to"),
                    "confidence": x.get("confidence", "UNKNOWN"), "fact": x.get("fact") or x.get("text") or ""})
    return out

def temporal_status(evidence: Dict[str, Any], now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    vf = _date(evidence.get("valid_from")); vt = _date(evidence.get("valid_to"))
    if vf and vf > now: return "PLANNED"
    if vt and vt < now: return "EXPIRED_OR_HISTORICAL"
    return "CURRENT_OR_UNDATED"

def _date(v: Any):
    if not v: return None
    s=str(v).replace("Z", "+00:00")
    try:
        d=datetime.fromisoformat(s)
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        return None

def assess_freshness(evidence: Iterable[Dict[str, Any]] | None) -> Dict[str, Any]:
    rows=normalize_evidence(evidence); conflicts=[]
    by_fact={}
    for r in rows:
        key=str(r["fact"]).strip().lower()
        if key: by_fact.setdefault(key, []).append(r)
    # Same subject with different fact text is left unresolved; callers should surface source disagreement.
    return {"count": len(rows), "items": [{**r, "temporal_status": temporal_status(r)} for r in rows],
            "conflict_policy": "Không tự động chọn nguồn khi có mâu thuẫn; hiển thị chênh lệch và yêu cầu kiểm chứng.",
            "has_expired_or_historical": any(temporal_status(r)=="EXPIRED_OR_HISTORICAL" for r in rows),
            "conflicts": conflicts}
