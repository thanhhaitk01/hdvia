"""HDVIA 1.30.1 travel ontology.
Multi-label object classification for tourism knowledge and guide operations.
"""
from __future__ import annotations
from typing import Any, Dict, Iterable, List
import re

OBJECT_TYPES = {
    "FESTIVAL", "RELIGIOUS_SITE", "HERITAGE_SITE", "HISTORICAL_SITE",
    "INTANGIBLE_HERITAGE", "DOCUMENTARY_HERITAGE", "NATURAL_SITE", "FOOD",
    "CRAFT_VILLAGE", "PERSON", "CITY_OR_DESTINATION", "EVENT", "TOUR",
    "HOTEL", "RESTAURANT", "ATTRACTION", "CULTURAL_PRACTICE", "LOCAL_PRODUCT",
    "UNKNOWN",
}

RULES = [
    ("FESTIVAL", ("lễ hội", "festival", "ngày hội", "hội làng", "hội xuân")),
    ("EVENT", ("sự kiện", "event", "chương trình", "triển lãm", "concert", "show")),
    ("RELIGIOUS_SITE", ("đền", "chùa", "miếu", "đình", "am", "nhà thờ", "thánh đường", "tịnh xá", "thiền viện")),
    ("HISTORICAL_SITE", ("di tích lịch sử", "thành cổ", "thành nhà", "lăng", "căn cứ", "địa đạo", "kinh thành")),
    ("HERITAGE_SITE", ("di tích", "di sản", "phố cổ", "cung điện", "tháp", "khu di tích", "cố đô")),
    ("INTANGIBLE_HERITAGE", ("di sản phi vật thể", "ca trù", "quan họ", "đờn ca tài tử", "hát xoan", "bài chòi")),
    ("DOCUMENTARY_HERITAGE", ("di sản tư liệu", "mộc bản", "châu bản", "bia tiến sĩ", "tư liệu lưu trữ")),
    ("NATURAL_SITE", ("hồ", "núi", "sông", "suối", "thác", "hang", "động", "vườn quốc gia", "bãi biển", "đảo", "vịnh", "đèo", "rừng")),
    ("FOOD", ("bánh", "món ăn", "ẩm thực", "đặc sản", "mì", "phở", "bún", "chè", "nem", "mắm", "quán ăn")),
    ("RESTAURANT", ("nhà hàng", "restaurant", "quán ăn", "quán đặc sản")),
    ("CRAFT_VILLAGE", ("làng nghề", "làng gốm", "làng đá", "làng chiếu", "làng lụa", "làng mộc")),
    ("PERSON", ("vua ", "chúa ", "tướng ", "danh nhân", "nhân vật lịch sử", "nhà thơ", "nhà văn", "anh hùng")),
    ("TOUR", ("tour", "chương trình tour", "hành trình", "gói du lịch")),
    ("HOTEL", ("khách sạn", "resort", "hotel", "homestay", "khu nghỉ dưỡng")),
    ("ATTRACTION", ("khu vui chơi", "công viên", "bảo tàng", "show", "cáp treo", "điểm check-in", "điểm tham quan")),
    ("LOCAL_PRODUCT", ("sản phẩm địa phương", "quà địa phương", "đặc sản làm quà", "hàng thủ công")),
    ("CULTURAL_PRACTICE", ("phong tục", "tập quán", "nghi lễ", "thực hành văn hóa", "tín ngưỡng")),
    ("CITY_OR_DESTINATION", ("thành phố", "tỉnh", "huyện", "thị xã", "địa danh", "điểm đến")),
]

def _norm(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip().lower()

def classify_multilabel(name: str, query: str = "", profile: Dict[str, Any] | None = None) -> Dict[str, Any]:
    text = _norm(f"{name} {query}")
    scores: Dict[str, int] = {}
    matched: Dict[str, List[str]] = {}
    for kind, terms in RULES:
        for term in terms:
            if _norm(term) in text:
                scores[kind] = scores.get(kind, 0) + (2 if " " in term.strip() else 1)
                matched.setdefault(kind, []).append(term)
    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    labels = [k for k, _ in ranked[:4]] or ["UNKNOWN"]
    if profile:
        hint = _norm(profile.get("type") or profile.get("object_type"))
        if hint in OBJECT_TYPES and hint not in labels:
            labels.insert(0, hint)
            labels = labels[:4]
    primary = labels[0]
    return {
        "primary_type": primary,
        "types": labels,
        "confidence": "HIGH" if scores.get(primary, 0) >= 3 else ("MEDIUM" if primary != "UNKNOWN" else "LOW"),
        "matched_terms": sorted(set(matched.get(primary, []))),
        "type_scores": scores,
    }
