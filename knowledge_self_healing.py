"""HDVIA self-healing knowledge loop.

Detects missing destination knowledge, acquires reference evidence from the
existing SmartKnowledgeAcquirer, persists it in a bounded reference cache,
and exposes the fresh evidence to the answer layer immediately. It never
promotes external evidence to VERIFIED/PUBLISHED knowledge automatically.
"""
from __future__ import annotations
import json, os, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from knowledge_expansion import KnowledgeExpansionEngine
from smart_knowledge_acquisition import SmartKnowledgeAcquirer

BASE = Path(__file__).resolve().parent
CACHE = BASE / "data" / "warehouse" / "smart_knowledge_cache.json"
MAX_PROFILES = int(os.getenv("HDVIA_SMART_CACHE_MAX_PROFILES", "5000"))


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _load() -> Dict[str, Any]:
    try:
        data = json.loads(CACHE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save(data: Dict[str, Any]) -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class KnowledgeSelfHealingEngine:
    VERSION = "1.1.0-deep-world-research-loop"

    def __init__(self, acquirer: Optional[SmartKnowledgeAcquirer] = None):
        self.acquirer = acquirer or SmartKnowledgeAcquirer()

    def inspect(self, name: str, *, profile: str = "general") -> Dict[str, Any]:
        curated = KnowledgeExpansionEngine().inspect(name, tourist_profile=profile)
        data = _load()
        key = _norm(name)
        cached = (data.get("profiles") or {}).get(key) if isinstance(data.get("profiles"), dict) else None
        gaps = list(curated.get("gaps") or [])
        if cached:
            # Reference cache can satisfy an answer-time evidence gap without
            # altering the curated warehouse's verified coverage.
            block_domains={str(b.get("domain") or "").lower() for b in (cached.get("knowledge_blocks") or []) if isinstance(b, dict)}
            gaps=[g for g in gaps if str(g.get("domain") if isinstance(g, dict) else g).lower() not in block_domains]
            if cached.get("wikipedia", {}).get("vi_extract"):
                gaps=[g for g in gaps if str(g.get("domain") if isinstance(g, dict) else g).lower() != "culture"]
            if cached.get("wikipedia", {}).get("en_extract"):
                gaps=[g for g in gaps if str(g.get("domain") if isinstance(g, dict) else g).lower() != "history"]
            if cached.get("osm", {}).get("results"):
                gaps=[g for g in gaps if str(g.get("domain") if isinstance(g, dict) else g).lower() != "geography"]
            if cached.get("representative_image"):
                gaps=[g for g in gaps if str(g.get("domain") if isinstance(g, dict) else g).lower() != "tourism"]
        return {
            "name": name,
            "curated_coverage": curated.get("coverage", {}),
            "gaps": gaps,
            "reference_profile": cached,
            "needs_acquisition": bool(gaps) or not cached,
            "version": self.VERSION,
        }

    def ensure(self, name: str, *, question: str = "", domain: str = "general", profile: str = "general") -> Dict[str, Any]:
        state = self.inspect(name, profile=profile)
        cached = state.get("reference_profile") or {}
        requested_domain = str(domain or "general").lower()
        mapping = {
            "history":"history", "culture":"culture", "food":"food", "nature":"nature",
            "people":"people", "economy":"economy", "tourism":"tourism", "destination":"tourism",
            "guide_script":"tourism", "festival":"festival", "shopping":"food", "religion":"culture", "landmarks":"landmarks", "general_qa":"general",
        }
        requested_domain = mapping.get(requested_domain, requested_domain)
        block_domains = {str(b.get("domain") or "").lower() for b in (cached.get("knowledge_blocks") or []) if isinstance(b, dict)}
        requested_satisfied = bool(cached) and (requested_domain == "general" or requested_domain in block_domains)
        cached_deep = bool(cached and str(cached.get("research_depth", "")).upper() == "DEEP")
        if cached and cached_deep and (not state["needs_acquisition"] or requested_satisfied):
            return {"ok": True, "changed": False, "state": state, "profile": cached, "status": "CACHE"}

        domains = [g.get("domain") if isinstance(g, dict) else g for g in (state.get("gaps") or [])]
        if requested_domain != "general" and requested_domain in domains:
            domains = [requested_domain] + [x for x in domains if x != requested_domain]
        domains = [str(x) for x in domains[:4] if x]
        acquired = self.acquirer.acquire(name, include_live=True, domains=domains, question=question, depth="deep")
        if not acquired.get("ok"):
            return {"ok": False, "changed": False, "state": state, "error": acquired.get("error", "acquisition_failed")}

        profile_data = acquired.get("profile") or {}
        data = _load()
        profiles = data.setdefault("profiles", {})
        profiles[_norm(name)] = profile_data
        if len(profiles) > MAX_PROFILES:
            ordered = sorted(profiles.items(), key=lambda kv: str((kv[1] or {}).get("acquired_at", "")), reverse=True)
            data["profiles"] = dict(ordered[:MAX_PROFILES])
        data["version"] = "2.0.0"
        data["updated_at"] = now()
        data["last_run"] = {"requested": 1, "ok": 1, "errors": 0, "target": name, "domains": domains}
        data["publication_policy"] = "REFERENCE_ONLY"
        _save(data)
        return {"ok": True, "changed": True, "state": self.inspect(name, profile=profile), "profile": profile_data, "status": "ACQUIRED"}


def reference_lines(profile: Dict[str, Any], *, domain: str = "general", limit: int = 6) -> list[str]:
    """Convert acquired reference evidence into concise answer-safe lines."""
    if not isinstance(profile, dict):
        return []
    out=[]
    wiki=profile.get("wikipedia") or {}
    blocks=profile.get("knowledge_blocks") or []
    wanted=str(domain or "general").upper()
    for block in blocks:
        if wanted not in {"GENERAL_QA","DESTINATION","GUIDE_SCRIPT","general"} and str(block.get("domain", "")).upper() not in {wanted, "GENERAL_QA"}:
            continue
        text=str(block.get("extract") or "").strip()
        if text:
            out.append(f"• {block.get('title') or profile.get('name')}: {text[:900]}")
    if not out and wiki.get("vi_extract"):
        out.append(f"• {profile.get('name')}: {str(wiki['vi_extract'])[:900]}")
    if wanted in {"PEOPLE", "FESTIVAL", "LANDMARKS", "GENERAL_QA", "DESTINATION"} or not out:
        for item in profile.get("related_entities") or []:
            label=item.get("label") or item.get("title")
            desc=item.get("description") or ""
            if label and desc:
                out.append(f"• {label}: {desc}")
                if len(out) >= limit: break
    if wanted in {"GENERAL_QA", "DESTINATION"} and len(out) < limit:
        for item in profile.get("web_sources") or []:
            snippet=item.get("extract") or item.get("snippet") or ""
            if snippet:
                out.append(f"• {item.get('title') or item.get('url')}: {str(snippet)[:700]}")
                if len(out) >= limit: break
    return out[:limit]
