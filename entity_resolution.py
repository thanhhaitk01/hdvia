"""Entity resolution bridge for HDVIA Knowledge Fusion.

Resolves Vietnamese travel-place mentions across OSM, Wikipedia and Wikidata
without changing the Journey UI or the canonical place names used by the engine.
The resolver is deliberately bounded and deterministic: it prefers explicit
aliases, then provider cross-links, then a small fuzzy token score.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, Iterable, List, Optional


def normalize(text: str) -> str:
    s = unicodedata.normalize("NFD", str(text or "").strip().lower())
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = s.replace("đ", "d")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def tokens(text: str) -> set[str]:
    return set(normalize(text).split())


# High-value cross-language landmark aliases. This is intentionally small;
# provider results are used to discover additional candidates at runtime.
CROSS_LANGUAGE_ALIASES = {
    "chua cau": ["Japanese Bridge", "Hoi An Japanese Bridge"],
    "chua cau hoi an": ["Japanese Bridge", "Hoi An Japanese Bridge"],
    "cau nhat ban hoi an": ["Japanese Bridge", "Hoi An Japanese Bridge"],
    "japanese bridge": ["Japanese Bridge"],
    "hoi an japanese bridge": ["Japanese Bridge", "Hoi An Japanese Bridge"],
    "thanh dia my son": ["My Son Sanctuary", "My Son"],
    "thanh dia my son hoi an": ["My Son Sanctuary", "My Son"],
    "ba na hills": ["Ba Na Hills", "Bana Hills"],
    "ba na hill": ["Ba Na Hills", "Bana Hills"],
}


class EntityResolver:
    VERSION = "1.25.2.3-entity-resolution"

    def __init__(self, adapter):
        self.adapter = adapter

    @staticmethod
    def _rows(result: Dict[str, Any]) -> List[Dict[str, Any]]:
        data = result.get("data") if isinstance(result, dict) else {}
        if not isinstance(data, dict):
            return []
        rows = data.get("search") or data.get("results") or []
        return [r for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []

    @staticmethod
    def _best(rows: Iterable[Dict[str, Any]], original: str) -> Optional[Dict[str, Any]]:
        q = tokens(original)
        scored=[]
        for row in rows:
            label = row.get("label") or row.get("name") or row.get("title") or ""
            desc = row.get("description") or row.get("snippet") or ""
            hay = tokens(f"{label} {desc}")
            score = len(q & hay)
            # Strong geographic relevance for Vietnam/Hoi An when present.
            desc_n = normalize(desc)
            if "vietnam" in desc_n: score += 2
            if "hoi an" in desc_n: score += 2
            if "bridge" in normalize(label) and "cau" in q: score += 1
            scored.append((score, row))
        if not scored:
            return None
        scored.sort(key=lambda x: (-x[0], str(x[1].get("id") or x[1].get("pageid") or "")))
        return scored[0][1]

    def resolve(self, name: str, *, wikipedia_vi: Optional[Dict[str, Any]] = None,
                wikipedia_en: Optional[Dict[str, Any]] = None,
                wikidata_direct: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        original = str(name or "").strip()
        normalized = normalize(original)
        queries: List[Dict[str, str]] = []
        candidates: List[str] = []

        for alias in CROSS_LANGUAGE_ALIASES.get(normalized, []):
            candidates.append(alias)
            queries.append({"query": alias, "reason": "cross_language_alias"})

        # Wikipedia English titles are a strong bridge from local Vietnamese
        # names to Wikidata's English labels.
        for result, reason in ((wikipedia_en, "wikipedia_en_title"), (wikipedia_vi, "wikipedia_vi_title")):
            for row in self._rows(result or {}):
                title = row.get("title") or row.get("name")
                if title and title not in candidates:
                    candidates.append(str(title))
                    queries.append({"query": str(title), "reason": reason})

        if original and original not in candidates:
            candidates.insert(0, original)
            queries.insert(0, {"query": original, "reason": "original"})

        # Try direct provider result first, then bounded candidate queries.
        result_rows=[]
        if wikidata_direct:
            result_rows.extend(self._rows(wikidata_direct))
        used=[]
        for q in candidates[:5]:
            if q in used:
                continue
            used.append(q)
            if q == original and wikidata_direct:
                continue
            try:
                r=self.adapter.wikidata(q, 5)
            except Exception:
                continue
            if isinstance(r, dict) and r.get("ok"):
                result_rows.extend(self._rows(r))

        # Deduplicate by entity id/label.
        seen=set(); unique=[]
        for row in result_rows:
            key=str(row.get("id") or row.get("wikibase_item") or row.get("pageid") or row.get("label") or row.get("title"))
            if key in seen: continue
            seen.add(key); unique.append(row)

        best=self._best(unique, original)
        if best:
            label=best.get("label") or best.get("name") or best.get("title")
            desc=best.get("description") or best.get("snippet")
            return {
                "input": original,
                "normalized": normalized,
                "canonical_name": original,
                "confidence": "HIGH" if (best.get("id") and ("vietnam" in normalize(desc or "") or any(normalize(label or "") == normalize(x) for x in candidates))) else "MEDIUM",
                "resolved_by": next((q["reason"] for q in queries if normalize(q["query"]) == normalize(label or "")), "provider_search"),
                "wikidata": {
                    "id": best.get("id") or best.get("wikibase_item"),
                    "label": label,
                    "description": desc,
                    "match": best.get("match"),
                },
                "queries": queries[:8],
            }

        return {
            "input": original,
            "normalized": normalized,
            "canonical_name": original,
            "confidence": "UNRESOLVED",
            "resolved_by": None,
            "wikidata": None,
            "queries": queries[:8],
        }
