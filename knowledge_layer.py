"""HDVIA Knowledge Layer V1.

A deterministic, reviewable knowledge retrieval layer for the Beta 1.8.4
assistant. This is retrieval from curated source data, not model training.
"""
import json
import os
import re
from functools import lru_cache

BASE = os.path.dirname(__file__)
KNOWLEDGE_FILE = os.path.join(BASE, "data", "knowledge_base.json")


def _tokens(text):
    return set(re.findall(r"[\wÀ-ỹĐđ]+", (text or "").lower(), flags=re.UNICODE))


@lru_cache(maxsize=1)
def load_knowledge():
    with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def search_knowledge(query, limit=5):
    """Return the most relevant curated entries using transparent token scoring."""
    q = _tokens(query)
    if not q:
        return []
    scored = []
    for item in load_knowledge().get("entries", []):
        hay = " ".join([
            item.get("title", ""), item.get("destination", ""),
            item.get("category", ""), item.get("summary", ""),
            " ".join(item.get("keywords", [])), item.get("content", "")
        ]).lower()
        t = _tokens(hay)
        score = len(q & t)
        # Destination/category matches are deliberately weighted higher.
        if item.get("destination", "").lower() in (query or "").lower():
            score += 3
        if item.get("category", "").lower() in (query or "").lower():
            score += 1
        if score:
            scored.append((score, item))
    scored.sort(key=lambda x: (-x[0], x[1].get("id", "")))
    return [item for _, item in scored[:limit]]


def answer_from_knowledge(query, limit=3):
    hits = search_knowledge(query, limit=limit)
    if not hits:
        return None, []
    lines = ["HDVIA tham chiếu các mục trong Kho tri thức đã được kiểm duyệt:"]
    for item in hits:
        lines.append(f"• {item['title']}: {item['summary']}")
    return "\n".join(lines), hits
