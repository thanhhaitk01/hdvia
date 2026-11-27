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
WAREHOUSE_KPD_FILE = os.path.join(BASE, "data", "warehouse", "khamphadisan_seed_2026.json")



@lru_cache(maxsize=1)
def load_reference_warehouse():
    """Load compact, source-attributed reference records for destination QA.

    These are not model-training data and are not treated as verified facts merely
    because they came from an editorial travel source.
    """
    try:
        with open(WAREHOUSE_KPD_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("records", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _tokens(text):
    return set(re.findall(r"[\wÀ-ỹĐđ]+", (text or "").lower(), flags=re.UNICODE))


@lru_cache(maxsize=1)
def load_knowledge():
    with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


@lru_cache(maxsize=1)
def _knowledge_index():
    """Pre-tokenize curated entries so repeated HDV questions stay fast.

    The index is deterministic and read-only; it changes retrieval performance,
    not the underlying knowledge or ranking semantics.
    """
    rows=[]
    for item in list(load_knowledge().get("entries", [])) + load_reference_warehouse():
        hay = " ".join([
            item.get("title", ""), item.get("destination", ""),
            item.get("category", ""), item.get("summary", ""),
            " ".join(item.get("keywords", [])), item.get("content", "")
        ]).lower()
        if not item.get("summary"):
            item = {**item, "summary": item.get("content", "")[:600], "id": item.get("id") or item.get("knowledge_id", "")}
        rows.append((item, _tokens(hay)))
    return tuple(rows)


@lru_cache(maxsize=4096)
def _search_knowledge_cached(query_norm: str, limit: int, intent: str = ""): 
    """Rank evidence by semantic signals instead of raw token count.

    Signals: exact phrase, place/topic overlap, curated-source priority and
    freshness/status. This is deterministic retrieval, not model training.
    """
    q = _tokens(query_norm)
    if not q:
        return ()
    intent_map = {
        "HISTORY": {"lịch sử", "di sản", "triều đại", "vua", "chiến tranh"},
        "CULTURE": {"văn hóa", "phong tục", "truyền thống", "di sản"},
        "FOOD": {"ẩm thực", "món ăn", "đặc sản", "ăn gì", "nhà hàng"},
        "GUIDE_SCRIPT": {"thuyết minh", "giới thiệu", "kịch bản", "nói với khách"},
        "DESTINATION": {"điểm đến", "tham quan", "nổi tiếng", "có gì", "check-in"},
        "EXPERIENCE": {"kinh nghiệm", "trải nghiệm", "mẹo", "lưu ý"},
        "FESTIVAL": {"lễ hội", "sự kiện", "ngày hội"},
        "CURRENT_EVENTS": {"hôm nay", "ngày mai", "đang diễn ra", "sự kiện"},
        "ITINERARY": {"lịch trình", "hành trình", "3 ngày", "4 ngày", "5 ngày"},
    }
    wanted = intent_map.get(intent, set())
    scored = []
    for item, t in _knowledge_index():
        title = (item.get("title") or "").lower()
        dest = (item.get("destination") or item.get("place") or "").lower()
        topic = (item.get("category") or item.get("topic") or "").lower()
        keywords = " ".join(item.get("keywords", [])).lower()
        hay = " ".join([title, dest, topic, keywords, item.get("summary", ""), item.get("content", "")]).lower()
        overlap = len(q & t)
        if not overlap:
            continue
        score = overlap * 1.0
        # Exact phrase is a much stronger signal than isolated words.
        if query_norm in hay:
            score += 4.0
        for phrase in wanted:
            if phrase in hay:
                score += 1.5
        if dest and dest in query_norm:
            score += 3.0
        if topic and any(tok in topic for tok in q):
            score += 1.0
        status = str(item.get("status", "VERIFIED")).upper()
        source = str(item.get("source", ""))
        if source == "HDVIA Destination Catalog":
            score += 2.0
        elif status == "REFERENCE":
            score += 0.5
        elif status == "DISCOVERY_SOURCE":
            score -= 0.25
        scored.append((score, item))
    scored.sort(key=lambda x: (-x[0], x[1].get("id", x[1].get("knowledge_id", ""))))
    return tuple(item for _, item in scored[:limit])



def _norm(s):
    return " ".join(re.findall(r"[\wÀ-ỹĐđ]+", (s or "").lower(), flags=re.UNICODE))


@lru_cache(maxsize=4096)
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

def search_knowledge(query, limit=5, intent=None):
    """Return relevant curated entries with deterministic cached retrieval."""
    query_norm = _norm(query)
    if not query_norm:
        return []
    result = list(_search_knowledge_cached(query_norm, limit, intent or ""))
    # Always retain a catalog/province identity hit when the place is known;
    # editorial references must not crowd out the authoritative coverage registry.
    catalog_hits = catalog_entries(query)
    if catalog_hits and not any((h.get("source") in ("HDVIA Vietnam Coverage Registry", "HDVIA Destination Catalog") or str(h.get("id","")).startswith(("catalog-","province-"))) for h in result):
        if len(result) >= limit:
            result = result[:max(0, limit-1)] + catalog_hits[:1]
        else:
            result.append(catalog_hits[0])

    if len(result) < limit:
        seen={item.get("id") for item in result}
        for item in load_reference_warehouse():
            hay = _tokens(" ".join([item.get("title",""), item.get("place",""), item.get("topic",""), item.get("content",""), " ".join(item.get("keywords",[]))]))
            if query_norm and len(_tokens(query_norm) & hay) > 0 and item.get("knowledge_id") not in seen:
                result.append({**item, "id": item.get("knowledge_id"), "category": item.get("topic"), "summary": item.get("content",""), "destination": item.get("place",""), "status": item.get("status"), "source_type":"editorial_reference"})
                seen.add(item.get("knowledge_id"))
                if len(result)>=limit: break
        for item in catalog_hits:
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
