"""Unified Hanh Trinh AI search.

One input can resolve either a destination/place question or a multi-stop itinerary.
The resolver reads curated catalog data, 34-province administrative master data,
knowledge records and the linked 8-warehouse Data Core when available.
"""
from __future__ import annotations
import re
import unicodedata
from typing import Any, Dict, List

from destination_catalog import DESTINATIONS
from province_data import PROVINCES_2025
from knowledge_layer import search_knowledge


def norm(text: str) -> str:
    text = unicodedata.normalize("NFD", str(text or "").lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", text.replace("đ", "d")).strip()


def _score(query: str, values: List[str]) -> int:
    q = norm(query)
    if not q:
        return 0
    q_tokens = {t for t in q.split() if len(t) >= 3}
    score = 0
    for value in values:
        v = norm(value)
        if not v:
            continue
        if v == q:
            score = max(score, 100)
        elif v and v in q and len(v) >= 3:
            score = max(score, 90)
        elif q and q in v and len(q) >= 3:
            score = max(score, 80)
        else:
            overlap = q_tokens & {t for t in v.split() if len(t) >= 3}
            if len(overlap) >= 2:
                score = max(score, 45 + len(overlap) * 5)
    return score


def classify_query(query: str) -> str:
    q = norm(query)
    itinerary_markers = ["ngay", "hanh trinh", "lich trinh", "tour", "di qua", "den", "ve lai"]
    if "->" in query or "→" in query or any(m in q for m in itinerary_markers) and len(q.split()) >= 4:
        return "ITINERARY"
    return "PLACE"


def unified_search(query: str, *, warehouse_context: Dict[str, List[Dict[str, Any]]] | None = None) -> Dict[str, Any]:
    q = str(query or "").strip()
    if not q:
        return {"intent": "EMPTY", "query": q, "matches": [], "context": {}}

    intent = classify_query(q)
    destination_hits: List[Dict[str, Any]] = []
    province_hits: List[Dict[str, Any]] = []

    for d in DESTINATIONS:
        score = _score(q, [d.get("name", ""), d.get("slug", ""), *(d.get("highlights") or [])])
        if score >= 15:
            destination_hits.append({"score": score, "record": d})
    destination_hits.sort(key=lambda x: -x["score"])

    for p in PROVINCES_2025:
        score = _score(q, [p.get("name", ""), p.get("slug", ""), *(p.get("aliases") or []), *(p.get("tourism_hubs") or [])])
        if score >= 15:
            province_hits.append({"score": score, "record": p})
    province_hits.sort(key=lambda x: -x["score"])

    knowledge = search_knowledge(q, limit=8)
    linked = warehouse_context or {}
    linked_hits = []
    for kind, rows in linked.items():
        if kind == "lineage":
            continue
        for row in rows:
            hay = [row.get("name"), row.get("title"), row.get("place"), row.get("topic"), row.get("content"), row.get("insight")]
            score = _score(q, [str(v) for v in hay if v])
            if score:
                linked_hits.append({"score": score, "kind": kind, "record": row})
    linked_hits.sort(key=lambda x: -x["score"])

    parent = destination_hits[0]["record"] if destination_hits else None
    if not parent and province_hits:
        pn = norm(province_hits[0]["record"].get("name", ""))
        for d in DESTINATIONS:
            if pn and pn in norm(d.get("name", "")):
                parent = d
                break

    related_destinations = destination_hits[:8]
    if parent and not related_destinations:
        related_destinations = [{"score": 100, "record": parent}]
    if province_hits:
        # Province-level searches should not surface unrelated national destinations.
        # The province master data already carries compact tourism hubs for the UI.
        province_top = province_hits[0]["record"]
        province_name = norm(province_top.get("name", ""))
        exact_dest = [x for x in destination_hits if province_name in norm(x["record"].get("name", ""))]
        if exact_dest:
            related_destinations = exact_dest[:8]

    context = {
        "primary_destination": parent,
        "provinces": [x["record"] for x in province_hits[:5]],
        "destinations": [x["record"] for x in related_destinations[:10]],
        "knowledge": knowledge,
        "warehouse": linked_hits[:20],
    }
    return {
        "intent": intent,
        "query": q,
        "summary": _summary(q, intent, parent, province_hits, destination_hits, knowledge),
        "context": context,
        "matches": destination_hits[:10],
    }


def _summary(q, intent, parent, province_hits, destination_hits, knowledge):
    if intent == "ITINERARY":
        return "HDVIA nhận diện đây là yêu cầu về hành trình và sẽ kết hợp phân tích lịch trình với dữ liệu điểm đến, thời tiết, rủi ro và kinh nghiệm HDV."
    if parent:
        return f"HDVIA nhận diện {q} là điểm đến/địa danh liên quan đến {parent.get('name')}."
    if province_hits:
        return f"HDVIA nhận diện {q} là khu vực hành chính/điểm đến và đang tổng hợp dữ liệu liên quan."
    if knowledge:
        return f"HDVIA đã tìm thấy {len(knowledge)} nội dung tri thức liên quan đến {q}."
    if destination_hits:
        return f"HDVIA tìm thấy {len(destination_hits)} điểm đến phù hợp với {q}."
    return f"Chưa có dữ liệu đủ mạnh cho {q}. Hãy kiểm tra lại tên điểm đến hoặc thử từ khóa cụ thể hơn."
