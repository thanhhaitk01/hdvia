"""HDVIA 1.30.1 Travel Story Graph: connect entities into guideable narratives."""
from __future__ import annotations
from typing import Any, Dict, List
import re

RELATION_HINTS = [
    ("located_in", ("ở", "thuộc", "tại")),
    ("associated_with", ("gắn với", "liên quan", "thờ", "tưởng niệm")),
    ("happened_at", ("diễn ra tại", "tại lễ hội", "tại")),
    ("part_of", ("thuộc", "nằm trong", "một phần của")),
    ("connected_to", ("gắn với", "liên hệ với", "kết nối với")),
]

def build_story_graph(name: str, profile: Dict[str, Any] | None = None, query: str = "") -> Dict[str, Any]:
    p = profile or {}
    entities: List[Dict[str, Any]] = [{"name": name, "type": p.get("type") or p.get("primary_type") or "UNKNOWN"}]
    relations: List[Dict[str, Any]] = []
    # Explicit graph facts are preferred; free-text hints are only weak links.
    for fact in p.get("related_entities") or p.get("relations") or []:
        if not isinstance(fact, dict):
            continue
        target = str(fact.get("target") or fact.get("name") or "").strip()
        if not target or target.lower() == name.lower():
            continue
        entities.append({"name": target, "type": fact.get("type", "UNKNOWN")})
        relations.append({"from": name, "relation": fact.get("relation", "connected_to"), "to": target,
                          "confidence": fact.get("confidence", "REFERENCE")})
    # Common profile buckets can seed useful story nodes without inventing facts.
    buckets = (("people", "PERSON", "associated_with"), ("places", "PLACE", "connected_to"),
               ("events", "EVENT", "associated_with"), ("heritage", "HERITAGE_SITE", "part_of"))
    for key, typ, rel in buckets:
        for item in p.get(key) or []:
            if isinstance(item, str) and item.strip():
                target = item.strip()
            elif isinstance(item, dict):
                target = str(item.get("name") or "").strip()
            else:
                target = ""
            if target and not any(e["name"].lower() == target.lower() for e in entities):
                entities.append({"name": target, "type": typ})
                relations.append({"from": name, "relation": rel, "to": target, "confidence": "PROFILE"})
    entities = _dedupe_entities(entities)
    return {"version": "1.30.1", "root": name, "entities": entities, "relations": relations,
            "narrative_order": _narrative_order(name, entities, relations),
            "story_ready": len(entities) > 1}

def _dedupe_entities(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out, seen = [], set()
    for x in items:
        k = str(x.get("name", "")).strip().lower()
        if k and k not in seen:
            seen.add(k); out.append(x)
    return out

def _narrative_order(root: str, entities: List[Dict[str, Any]], relations: List[Dict[str, Any]]) -> List[str]:
    # Deterministic, guide-friendly: root → person/history → event → place/experience.
    rank = {"PERSON": 1, "HERITAGE_SITE": 2, "HISTORICAL_SITE": 2, "EVENT": 3, "FESTIVAL": 3,
            "PLACE": 4, "CITY_OR_DESTINATION": 4, "FOOD": 5, "ATTRACTION": 5, "UNKNOWN": 6}
    others = [e for e in entities if e["name"].lower() != root.lower()]
    others.sort(key=lambda e: (rank.get(e.get("type"), 6), e["name"]))
    return [root] + [e["name"] for e in others]
