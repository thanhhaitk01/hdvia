"""HDVIA 1.30 — Travel Intelligence Brain.

The brain sits between acquisition and presentation. It converts a resolved
place/query into a tourism-specific decision brief for tour guides: what the
object is, what to research, what matters to guests, operational risks,
what a guide can say, and what remains uncertain.

It is intentionally deterministic and evidence-aware. It does not invent facts;
unknown fields become research gaps. UI modules can consume the structured
output without changing the core reasoning layer.
"""
from __future__ import annotations
import re
from typing import Any, Dict, Iterable, List
from travel_ontology import classify_multilabel
from travel_story_graph import build_story_graph
from hdv_experience_brief import build_hdv_brief
from guide_decision_engine import assess_and_act
from source_freshness import assess_freshness
from hdv_experience_memory import build_experience_memory
from guide_route_decision import evaluate_route_time
from source_conflict_resolution import detect_conflicts

VERSION = "1.30.1-hdv-giau-kinh-nghiem"

OBJECT_RULES = [
    ("FESTIVAL", ("lễ hội", "festival", "ngày hội", "hội làng", "sự kiện văn hóa")),
    ("RELIGIOUS_SITE", ("đền", "chùa", "miếu", "đình", "am", "thánh thất", "nhà thờ", "thánh đường", "tịnh xá", "thiền viện")),
    ("HERITAGE_SITE", ("di tích", "di sản", "thành cổ", "thành nhà", "lăng", "cung điện", "tháp", "phố cổ")),
    ("NATURAL_SITE", ("hồ", "núi", "sông", "suối", "thác", "hang", "động", "vườn quốc gia", "bãi biển", "đảo", "vịnh", "đèo", "rừng")),
    ("FOOD", ("bánh", "món ăn", "ẩm thực", "đặc sản", "mì", "phở", "bún", "chè", "nem", "mắm")),
    ("CRAFT_VILLAGE", ("làng nghề", "làng gốm", "làng đá", "làng chiếu", "làng lụa", "làng mộc")),
    ("PERSON", ("vua ", "chúa ", "tướng ", "danh nhân", "nhân vật lịch sử", "nhà thơ", "nhà văn", "anh hùng")),
    ("CITY_OR_DESTINATION", ("thành phố", "tỉnh", "huyện", "thị xã", "địa danh", "điểm đến")),
]

RESEARCH_MAP = {
    "FESTIVAL": ["nguồn gốc", "thời gian", "địa điểm", "nghi lễ", "hoạt động", "cộng đồng", "quy mô", "an toàn", "giao thông", "thời tiết"],
    "RELIGIOUS_SITE": ["lịch sử", "nguồn gốc tín ngưỡng", "nhân vật liên quan", "kiến trúc", "nghi lễ", "quy tắc ứng xử", "giờ tham quan", "thời tiết", "tiếp cận"],
    "HERITAGE_SITE": ["lịch sử", "niên đại", "nhân vật", "kiến trúc", "giá trị di sản", "câu chuyện thuyết minh", "quy định tham quan", "thời tiết"],
    "NATURAL_SITE": ["địa lý", "hệ sinh thái", "cảnh quan", "hoạt động", "điều kiện đường đi", "thời tiết", "gió/mưa", "an toàn", "bảo tồn"],
    "FOOD": ["nguồn gốc", "nguyên liệu", "cách chế biến", "cách thưởng thức", "địa phương", "câu chuyện văn hóa", "dị ứng/kiêng kỵ cần lưu ý"],
    "CRAFT_VILLAGE": ["lịch sử", "nghề truyền thống", "sản phẩm", "quy trình", "người làm nghề", "trải nghiệm", "mua sắm", "bảo tồn"],
    "PERSON": ["tiểu sử", "bối cảnh lịch sử", "đóng góp", "địa điểm liên quan", "câu chuyện có nguồn", "những điểm cần tránh suy diễn"],
    "CITY_OR_DESTINATION": ["địa lý", "lịch sử", "văn hóa", "kinh tế", "điểm tham quan", "ẩm thực", "thời tiết", "giao thông", "sự kiện"],
    "UNKNOWN": ["định danh", "địa lý", "lịch sử", "văn hóa", "du lịch", "thời tiết", "an toàn"],
}

GUEST_VALUE = {
    "FESTIVAL": ["Ý nghĩa của lễ hội", "Điểm đặc sắc khách có thể quan sát", "Thời điểm nên đưa khách đến", "Những điều HDV cần nhắc trước khi vào khu vực đông người"],
    "RELIGIOUS_SITE": ["Câu chuyện nguồn gốc dễ hiểu", "Ý nghĩa tín ngưỡng và kiến trúc", "Quy tắc ứng xử", "Điểm nên quan sát khi thuyết minh"],
    "HERITAGE_SITE": ["Câu chuyện lịch sử nổi bật", "Chi tiết kiến trúc đáng xem", "Nhân vật và sự kiện liên quan", "Cách kể để khách dễ nhớ"],
    "NATURAL_SITE": ["Cảnh quan nổi bật", "Trải nghiệm phù hợp", "Điều kiện thời tiết/đường đi", "Quy tắc bảo vệ môi trường"],
    "FOOD": ["Câu chuyện món ăn", "Nguyên liệu và cách thưởng thức", "Điểm khác biệt địa phương", "Lưu ý khẩu vị và dị ứng"],
    "CRAFT_VILLAGE": ["Câu chuyện người làm nghề", "Quy trình tạo sản phẩm", "Giá trị văn hóa", "Cách mua hàng hợp lý và có nguồn gốc"],
    "PERSON": ["Bối cảnh nhân vật", "Đóng góp nổi bật", "Địa điểm gắn với nhân vật", "Một câu chuyện ngắn có nguồn"],
    "CITY_OR_DESTINATION": ["Bức tranh tổng quan", "Điểm nổi bật", "Câu chuyện địa phương", "Điều kiện thực tế cho chuyến đi"],
    "UNKNOWN": ["Xác định đúng đối tượng", "Thông tin nền", "Điều khách thực sự cần biết", "Điều kiện thực tế trước khi đi"],
}

RISK_RULES = [
    ("mưa lớn", "Cân nhắc hoạt động ngoài trời và chuẩn bị phương án thay thế."),
    ("gió mạnh", "Không nên xem nhẹ hoạt động trên sông/biển/đi thuyền; kiểm tra điều kiện thực tế trước khi khởi hành."),
    ("dông", "Ưu tiên an toàn, tránh khu vực trống trải hoặc hoạt động ngoài trời khi có cảnh báo phù hợp."),
    ("nóng", "Nhắc khách chuẩn bị nước, che nắng và điều chỉnh thời lượng hoạt động ngoài trời."),
]


def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def _dedupe(values: Iterable[str]) -> List[str]:
    out, seen = [], set()
    for value in values:
        value = str(value or "").strip()
        key = _norm(value)
        if value and key not in seen:
            seen.add(key)
            out.append(value)
    return out


def classify_object(name: str, query: str = "", profile: Dict[str, Any] | None = None) -> Dict[str, Any]:
    text = _norm(" ".join([str(name or ""), str(query or "")]))
    scores: Dict[str, int] = {}
    matched: Dict[str, List[str]] = {}
    for kind, terms in OBJECT_RULES:
        for term in terms:
            if _norm(term) in text:
                scores[kind] = scores.get(kind, 0) + (2 if " " in term.strip() else 1)
                matched.setdefault(kind, []).append(term)
    if profile:
        domains = {_norm(x) for x in (profile.get("domains_researched") or [])}
        domain_boost = {
            "festival": "FESTIVAL", "culture": "RELIGIOUS_SITE", "history": "HERITAGE_SITE",
            "nature": "NATURAL_SITE", "food": "FOOD", "people": "PERSON"
        }
        for d, kind in domain_boost.items():
            if d in domains:
                scores[kind] = scores.get(kind, 0) + 1
    if scores:
        kind = max(scores, key=scores.get)
        confidence = "HIGH" if scores[kind] >= 3 else "MEDIUM"
    else:
        kind, confidence = "UNKNOWN", "LOW"
    return {
        "type": kind,
        "confidence": confidence,
        "matched_terms": _dedupe(matched.get(kind, [])),
        "competing_types": sorted([k for k in scores if k != kind], key=lambda k: -scores[k])[:3],
    }


def _weather_signals(weather: Any) -> Dict[str, Any]:
    rows = [x for x in (weather or []) if isinstance(x, dict)]
    rain = [x.get("rain") for x in rows if isinstance(x.get("rain"), (int, float))]
    wind = [x.get("wind") or x.get("wind_kmh") for x in rows if isinstance(x.get("wind") or x.get("wind_kmh"), (int, float))]
    tmax = [x.get("tmax") for x in rows if isinstance(x.get("tmax"), (int, float))]
    codes = [x.get("weather_code") for x in rows]
    return {
        "max_rain_probability": max(rain) if rain else None,
        "max_wind_kmh": max(wind) if wind else None,
        "max_temperature_c": max(tmax) if tmax else None,
        "severe_weather_codes": [c for c in codes if c in (95, 96, 99)],
        "days": len(rows),
    }


def build_travel_brain(name: str, *, query: str = "", profile: Dict[str, Any] | None = None,
                       weather: Any = None, admin: Dict[str, Any] | None = None) -> Dict[str, Any]:
    profile = profile or {}
    admin = admin or {}
    obj = classify_object(name, query, profile)
    ontology = classify_multilabel(name, query, profile)
    # Preserve the 1.30 single-label contract while adding richer multi-label intelligence.
    obj["primary_type"] = ontology["primary_type"]
    obj["types"] = ontology["types"]
    obj["ontology_confidence"] = ontology["confidence"]
    kind = obj["type"]
    weather_signal = _weather_signals(weather)

    research = list(RESEARCH_MAP.get(kind, RESEARCH_MAP["UNKNOWN"]))
    sources = _dedupe(profile.get("sources") or [])
    gaps = []
    for key in ("coordinates", "knowledge_blocks", "sources", "representative_image"):
        value = profile.get(key)
        if not value:
            gaps.append({
                "field": key,
                "severity": "MEDIUM" if key in ("coordinates", "knowledge_blocks") else "LOW",
                "message": f"Chưa có đủ dữ liệu {key}; cần tiếp tục nghiên cứu/kiểm chứng."
            })

    actions = []
    if weather_signal["max_rain_probability"] is not None and weather_signal["max_rain_probability"] >= 45:
        actions.append("Chuẩn bị áo mưa/bao chống nước cho điện thoại và thiết bị của HDV.")
    if weather_signal["max_rain_probability"] is not None and weather_signal["max_rain_probability"] >= 70:
        actions.append("Chuẩn bị phương án B cho hoạt động ngoài trời.")
    if weather_signal["max_wind_kmh"] is not None and weather_signal["max_wind_kmh"] >= 30:
        actions.append("Kiểm tra lại điều kiện gió trước hoạt động ngoài trời; hoạt động trên nước cần xác nhận an toàn trước khi cho khách tham gia.")
    if weather_signal["max_temperature_c"] is not None and weather_signal["max_temperature_c"] >= 35:
        actions.append("Nhắc khách uống nước, chống nắng và giảm thời lượng đứng ngoài trời khi cần.")
    if weather_signal["severe_weather_codes"]:
        actions.append("Có tín hiệu thời tiết nguy hiểm; ưu tiên kiểm tra cảnh báo chính thức trước khi tổ chức hoạt động.")
    if not actions:
        actions.append("Kiểm tra điều kiện thực tế ngay trước khi đưa đoàn vào hoạt động.")

    guest_points = GUEST_VALUE.get(kind, GUEST_VALUE["UNKNOWN"])
    briefing = [
        f"Đối tượng: {kind.replace('_', ' ').title()}.",
        f"Mục tiêu của HDV: {guest_points[0].lower()} và chọn 1–2 câu chuyện có nguồn để giới thiệu, thay vì dồn quá nhiều dữ kiện.",
    ]
    if admin.get("commune"):
        briefing.append(f"Liên hệ địa phương: {admin.get('commune')}" + (f" · {admin.get('province')}" if admin.get("province") else "") + ".")
    if sources:
        briefing.append("Nguồn đang được hệ thống sử dụng: " + ", ".join(sources[:5]) + ".")
    briefing.append("Nếu thông tin có độ tin cậy thấp hoặc nguồn mâu thuẫn, HDVIA phải đánh dấu để HDV kiểm tra trước khi thuyết minh.")

    story_graph = build_story_graph(name, profile, query=query)
    hdv_brief = build_hdv_brief(name, ontology, {**profile, "knowledge_gaps": [g["message"] for g in gaps]}, story_graph)
    decision = assess_and_act(ontology["primary_type"], weather_signal, profile.get("crowd_level"), profile.get("guest_profile"), profile.get("operational"))
    evidence_rows = profile.get("evidence") or []
    freshness = assess_freshness(evidence_rows)
    conflict = detect_conflicts(evidence_rows)
    route_decision = evaluate_route_time(ontology["primary_type"], profile.get("operational"), weather_signal, profile.get("guest_profile"))
    experience_memory = build_experience_memory(ontology["primary_type"], weather_signal, profile.get("guest_profile"), profile.get("operational"), profile.get("experience_lessons"))

    return {
        "version": VERSION,
        "object": obj,
        "ontology": ontology,
        "research_plan": research,
        "guest_value": guest_points,
        "guide_brief": briefing,
        "operational_actions": _dedupe(actions),
        "weather_signals": weather_signal,
        "local_context": admin,
        "knowledge_gaps": gaps,
        "evidence": {"sources": sources, "confidence": profile.get("confidence", "UNKNOWN"), "status": profile.get("status", "UNKNOWN")},
        "decision_rule": "Nguồn + bối cảnh + thời tiết + rủi ro → ưu tiên an toàn → đề xuất cách phục vụ khách → nêu rõ khoảng trống dữ liệu.",
        "travel_story_graph": story_graph,
        "hdv_experience_brief": hdv_brief,
        "guide_decision": decision,
        "source_freshness": freshness,
        "source_conflicts": conflict,
        "route_time_decision": route_decision,
        "experience_memory": experience_memory,
        "experience_mode": "HDV_GIAU_KINH_NGHIEM",
    }
