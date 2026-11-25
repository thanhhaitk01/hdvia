"""HDVIA Knowledge Layer V1.

A deterministic, reviewable knowledge retrieval layer for the Beta 1.8.4
assistant. This is retrieval from curated source data, not model training.
"""
import json
import os
import re
from functools import lru_cache

from destination_catalog import DESTINATIONS
from province_data import PROVINCES_2025

BASE = os.path.dirname(__file__)
KNOWLEDGE_FILE = os.path.join(BASE, "data", "knowledge_base.json")


def _tokens(text):
    return set(re.findall(r"[\wÀ-ỹĐđ]+", (text or "").lower(), flags=re.UNICODE))


@lru_cache(maxsize=1)
def load_knowledge():
    with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data



def _norm(s):
    return " ".join(re.findall(r"[\wÀ-ỹĐđ]+", (s or "").lower(), flags=re.UNICODE))


def catalog_entries(query=""):
    """Return structured catalog knowledge when curated KB has no direct hit.

    This is intentionally limited to fields already present in the destination/province
    catalog. It never fabricates historical or cultural facts for a place that lacks
    curated fields.
    """
    q=_norm(query)
    out=[]
    for d in DESTINATIONS:
        names=[d.get("name", ""), d.get("slug", ""), *(d.get("highlights") or [])]
        if q and any(_norm(n) and _norm(n) in q for n in names):
            out.append({"id":"catalog-"+d["slug"],"destination":d["name"],"category":"Destination Catalog",
                        "title":d["name"]+" – hồ sơ điểm đến",
                        "summary":d.get("overview", ""), "content":d.get("overview", ""),
                        "keywords":names, "catalog":d, "source":"HDVIA Destination Catalog"})
    for p in PROVINCES_2025:
        names=[p.get("name", ""), *(p.get("aliases") or []), *(p.get("tourism_hubs") or [])]
        if q and any(_norm(n) and _norm(n) in q for n in names):
            out.append({"id":"province-"+p["slug"],"destination":p["name"],"category":"Vietnam Tourism Coverage",
                        "title":p["name"]+" – phạm vi du lịch",
                        "summary":f"{p.get('name','')} thuộc {p.get('region','')}. Các trung tâm/địa danh du lịch được registry nhận diện gồm: {', '.join(p.get('tourism_hubs') or [])}.",
                        "content":"Đây là dữ liệu nhận diện và phạm vi coverage; chưa phải bộ thuyết minh đã kiểm duyệt cho từng địa danh.",
                        "keywords":names, "catalog":p, "source":"HDVIA Vietnam Coverage Registry"})
    return out

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
    result=[item for _, item in scored[:limit]]
    if len(result) < limit:
        seen={item.get("id") for item in result}
        for item in catalog_entries(query):
            if item.get("id") not in seen:
                result.append(item); seen.add(item.get("id"))
                if len(result)>=limit: break
    return result


def answer_from_knowledge(query, limit=3):
    hits = search_knowledge(query, limit=limit)
    if not hits:
        return None, []
    lines = ["HDVIA tham chiếu các mục trong Kho tri thức đã được kiểm duyệt:"]
    for item in hits:
        lines.append(f"• {item['title']}: {item['summary']}")
    return "\n".join(lines), hits
