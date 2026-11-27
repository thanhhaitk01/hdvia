"""HDVIA Conversation Intelligence Layer.

Deterministic, provider-neutral conversation understanding for Beta releases.
It does not invent facts: answers are synthesized from the curated knowledge
layer and live Journey Intelligence context, while unknowns are surfaced as such.
"""
from __future__ import annotations
import os, re
from typing import Any, Dict, List, Tuple

from knowledge_layer import search_knowledge
from knowledge_self_healing import KnowledgeSelfHealingEngine, reference_lines
from province_data import PROVINCES_2025
from destination_catalog import DESTINATIONS
from coverage_registry import CATEGORIES, resolve_known_place
from journey_engine.engine import haversine_km

INTENTS = {
    "WEATHER": ("thời tiết", "mưa", "nhiệt độ", "nắng", "gió", "bão", "dông", "weather"),
    "HISTORY": ("lịch sử", "lịch sử hình thành", "vua", "triều đại", "chiến tranh"),
    "CULTURE": ("văn hóa", "phong tục", "truyền thống", "tập quán", "di sản"),
    "FOOD": ("ẩm thực", "món ăn", "đặc sản", "ăn gì", "quán ăn", "nhà hàng"),
    "GUIDE_SCRIPT": ("thuyết minh", "giới thiệu", "nói với khách", "bài thuyết minh", "kịch bản"),
    "ROUTE": ("lộ trình", "đi bao lâu", "mất bao lâu", "bao lâu để đi", "khoảng cách", "quãng đường", "di chuyển", "tuyến"),
    "ITINERARY": ("ngày 1", "ngày 2", "ngày 3", "ngày 4", "ngày 5", "lịch trình", "tour", "hành trình", "phân tích hành trình", "phân tích lịch trình", "đánh giá hành trình", "kiểm tra hành trình", "tối ưu hành trình"),
    "CURRENT_STATUS": ("hôm nay thế nào", "hôm nay ra sao", "hiện tại thế nào", "hiện tại ra sao", "bây giờ thế nào", "tình hình hôm nay"),
    "RISK": ("rủi ro", "cảnh báo", "nguy hiểm", "an toàn", "mưa bão", "đường xấu"),
    "PLAN_B": ("plan b", "phương án dự phòng", "thay thế", "nếu trời mưa", "nếu mưa"),
    "TOURIST_PROFILE": ("khách ấn", "khách hàn", "khách nhật", "khách trung", "khách quốc tế", "khách việt", "khách lớn tuổi", "trẻ em"),
    "EXPERIENCE": ("kinh nghiệm", "mẹo", "lưu ý", "nên làm gì", "gợi ý"),
    "DESTINATION": ("ở đâu", "có gì", "nổi tiếng", "điểm đến", "tham quan"),
    "KNOWLEDGE_GAP": ("chưa có dữ liệu", "chưa biết", "có nguồn không", "nguồn chính thức", "kiểm chứng"),
    "ECONOMY": ("kinh tế", "ngành kinh tế", "thu nhập", "sản xuất", "doanh nghiệp"),
    "PEOPLE": ("dân cư", "người dân", "dân số", "cộng đồng", "dân tộc"),
    "ADMIN": ("tỉnh", "thành phố", "hành chính", "địa giới", "đơn vị hành chính", "thuộc vùng", "vùng nào"),
    "RELIGION": ("tôn giáo", "tín ngưỡng", "thờ", "đền", "chùa", "nhà thờ"),
    "NATURE": ("thiên nhiên", "hệ sinh thái", "địa chất", "rừng", "hang động", "sông", "núi"),
    "TRANSPORT": ("giao thông", "sân bay", "bến xe", "tàu", "xe", "đường"),
    "SHOPPING": ("mua sắm", "đặc sản mua", "quà", "quà lưu niệm", "chợ", "mua"),
    "FESTIVAL": ("lễ hội", "sự kiện", "festival", "ngày hội"),
    "SUSTAINABILITY": ("du lịch bền vững", "môi trường", "rác thải", "bảo tồn"),
    "ACCOMMODATION": ("khách sạn", "lưu trú", "homestay", "resort", "nghỉ ở đâu", "ở đâu qua đêm"),
    "PRICE": ("giá bao nhiêu", "chi phí", "giá vé", "vé bao nhiêu", "ngân sách", "tốn bao nhiêu"),
    "OPENING_HOURS": ("mở cửa", "đóng cửa", "giờ mở cửa", "giờ tham quan", "giờ hoạt động"),
    "ACCESSIBILITY": ("người cao tuổi", "xe lăn", "trẻ em", "khó đi", "tiếp cận", "accessibility"),
    "ENTRY": ("visa", "thị thực", "nhập cảnh", "xuất nhập cảnh", "hộ chiếu", "hải quan"),
    "SERVICE": ("dịch vụ", "hướng dẫn viên", "đón tiễn", "đặt xe", "đặt tour", "đặt vé"),
    "TOURISM_MANAGEMENT": ("quản lý du lịch", "quy định du lịch", "giấy phép", "quy định tham quan", "hạn chế tham quan"),
    "CURRENT_EVENTS": ("sự kiện hôm nay", "sự kiện ngày mai", "đang diễn ra", "diễn ra hôm nay", "lịch sự kiện"),
}

FOLLOWUPS = {
    "WEATHER": ["Ngày nào cần lưu ý nhất?", "Nếu trời mưa thì nên đổi lịch thế nào?", "Có điểm nào phù hợp làm Plan B không?"],
    "HISTORY": ["Có câu chuyện nào hay để kể cho khách?", "Tóm tắt thành bài thuyết minh 3 phút được không?", "Khách quốc tế thường hỏi gì về nơi này?"],
    "CULTURE": ["Có phong tục nào HDV cần lưu ý?", "Điểm văn hóa nào đáng giới thiệu cho khách?", "Có điều gì không nên nói sai khi thuyết minh?"],
    "FOOD": ["Món nào nên giới thiệu cho khách quốc tế?", "Nên kết hợp ẩm thực với lịch trình thế nào?", "Có câu chuyện văn hóa nào gắn với món ăn không?"],
    "GUIDE_SCRIPT": ["Viết bài thuyết minh 3 phút cho điểm này.", "Cho tôi phiên bản dễ nói với khách quốc tế.", "Những câu hỏi khách thường hỏi là gì?"],
    "ROUTE": ["Chặng nào nên ưu tiên?", "Có cần chừa thêm thời gian dự phòng không?", "Nếu có sự cố giao thông thì phương án nào phù hợp?"],
    "ITINERARY": ["Thời tiết 7 ngày ở từng điểm thế nào?", "Lịch trình có điểm nào nên đổi thứ tự không?", "Plan B cho lịch trình này là gì?"],
    "RISK": ["Rủi ro này ảnh hưởng ngày nào?", "HDV nên chuẩn bị gì?", "Phương án thay thế là gì?"],
    "PLAN_B": ["Điểm trong nhà nào có thể thay thế?", "Nếu mưa cả ngày thì nên điều chỉnh ra sao?", "Có phương án ít di chuyển hơn không?"],
    "TOURIST_PROFILE": ["Khách này thường quan tâm điều gì?", "Nên thuyết minh theo cách nào?", "Có lưu ý văn hóa nào cho HDV không?"],
    "EXPERIENCE": ["Lưu ý quan trọng nhất cho HDV là gì?", "Có lỗi thường gặp nào cần tránh?", "Có thể áp dụng vào lịch trình hiện tại thế nào?"],
    "DESTINATION": ["Điểm nổi bật nhất để giới thiệu là gì?", "Có câu chuyện nào hay để thuyết minh về điểm này?", "Món ăn và trải nghiệm nào nên kết hợp?"],
    "ECONOMY": ["Ngành kinh tế nào nổi bật ở địa phương này?", "Thông tin kinh tế nào HDV có thể giới thiệu an toàn cho khách?"],
    "PEOPLE": ["Cộng đồng nào sinh sống và tạo nên bản sắc địa phương?", "Có lưu ý văn hóa nào khi giới thiệu về cộng đồng này?"],
    "ADMIN": ["Địa phương này thuộc vùng nào?", "Có thông tin hành chính nào cần xác minh trước khi thuyết minh?"],
    "RELIGION": ["Địa điểm tín ngưỡng này có ý nghĩa gì?", "HDV cần lưu ý gì khi giới thiệu không gian tôn giáo?"],
    "NATURE": ["Giá trị tự nhiên nổi bật là gì?", "Có yếu tố bảo tồn nào HDV cần lưu ý?"],
    "TRANSPORT": ["Có những cách di chuyển nào phù hợp?", "Thông tin giao thông nào cần dữ liệu LIVE trước khi tư vấn?"],
    "SHOPPING": ["Đặc sản nào có thể giới thiệu?", "Khi tư vấn mua sắm cần xác minh giá và nguồn gốc thế nào?"],
    "FESTIVAL": ["Lễ hội hoặc sự kiện nào nổi bật?", "Thông tin thời gian tổ chức cần xác minh từ nguồn nào?"],
    "SUSTAINABILITY": ["HDV nên hướng dẫn khách du lịch có trách nhiệm thế nào?", "Có điểm nào cần lưu ý về bảo tồn và môi trường?"],
}


def _norm(s: str) -> str:
    return " ".join(re.sub(r"[^\wÀ-ỹĐđ→>\- ]+", " ", (s or "").lower()).split())


def _requires_verified_detail(query: str, intent: str) -> bool:
    """Detect questions whose answer would require a specific verified fact.

    Destination metadata (overview/history/culture) is useful for orientation, but
    it must not be presented as an answer to a request for an exact event, year,
    person, date, number, or other pinpoint fact when no curated source supports it.
    """
    q=_norm(query)
    if intent not in ("HISTORY", "CULTURE", "GENERAL_QA", "GUIDE_SCRIPT"):
        return False
    patterns=(
        r"\bnăm\s+\d{3,4}\b", r"\bngày\s+\d{1,2}[/-]\d{1,2}\b",
        r"\bai\s+(là|đã|từng)\b", r"\bbao nhiêu\b", r"\bsố liệu\b",
        r"\btrận\b", r"\bhiệp định\b", r"\bsự kiện\b", r"\bnhân vật\b",
        r"\bchính xác\b", r"\btheo nguồn\b", r"\bnguồn chính thức\b"
    )
    return any(re.search(p, q) for p in patterns)


class ConversationIntelligenceEngine:
    VERSION = "1.2.0-smart-reasoning-point-intelligence"

    def __init__(self, external_enricher=None):
        self.external_enricher = external_enricher

    def set_external_enricher(self, external_enricher):
        self.external_enricher = external_enricher

    def detect_intents(self, query: str) -> List[str]:
        """Detect intents by evidence and rank the user's actual request first."""
        q = _norm(query)
        scores: Dict[str, int] = {}
        for intent, terms in INTENTS.items():
            score = sum(1 + (1 if len(term.split()) > 1 else 0) for term in terms if term in q)
            if score:
                scores[intent] = score
        boosts = {
            "ITINERARY": ("lập lịch trình", "lập hành trình", "phân tích hành trình", "phân tích lịch trình", "tối ưu hành trình", "kiểm tra hành trình"),
            "ROUTE": ("mất bao lâu", "bao lâu để đi", "khoảng cách", "quãng đường", "đi từ"),
            "WEATHER": ("thời tiết", "có mưa không", "mưa không", "nhiệt độ", "gió thế nào", "dự báo"),
            "CURRENT_STATUS": ("hôm nay thế nào", "hôm nay ra sao", "hiện tại thế nào", "bây giờ thế nào", "tình hình hôm nay"),
            "PLAN_B": ("nếu mưa", "nếu trời mưa", "plan b", "phương án dự phòng", "phương án thay thế"),
            "RISK": ("rủi ro", "cảnh báo", "nguy hiểm", "an toàn"),
        }
        for intent, markers in boosts.items():
            if any(marker in q for marker in markers):
                scores[intent] = scores.get(intent, 0) + 4

        # A compact route brief such as "Đà Nẵng - Hội An - Huế 3 ngày"
        # is still an itinerary request even when it contains none of the
        # explicit words "lịch trình" or "hành trình". Treat duration +
        # multiple recognized places as a strong itinerary signal.
        duration_match = re.search(r"\b\d{1,2}\s*(?:ngày|days?)\b", q)
        place_count = len(self.resolve_places(query))
        if duration_match and place_count >= 2:
            scores["ITINERARY"] = scores.get("ITINERARY", 0) + 6

        if not scores:
            return ["GENERAL_QA"]
        order={name:i for i,name in enumerate(INTENTS)}
        ranked=[k for k,_ in sorted(scores.items(), key=lambda kv:(-kv[1], order[kv[0]]))]
        if self.resolve_places(query) and "DESTINATION" not in ranked and not any(x in ranked for x in ("ITINERARY","WEATHER","CURRENT_STATUS","ROUTE","PLAN_B","RISK")):
            ranked.append("DESTINATION")
        return ranked[:4]

    def _primary_intent(self, query: str, intents: List[str]) -> str:
        """Choose the user's requested action, not incidental context words."""
        q=_norm(query)
        rules=(
            ("PLAN_B", ("nếu mưa", "nếu trời mưa", "plan b", "phương án dự phòng", "phương án thay thế")),
            ("ITINERARY", ("phân tích hành trình", "phân tích lịch trình", "đánh giá hành trình", "kiểm tra hành trình", "tối ưu hành trình", "lập lịch trình", "lập hành trình")),
            ("ROUTE", ("mất bao lâu", "bao lâu để đi", "khoảng cách", "quãng đường", "đi từ", "lộ trình")),
            ("RISK", ("rủi ro", "cảnh báo", "nguy hiểm", "an toàn", "đường xấu")),
            ("CURRENT_STATUS", ("hôm nay thế nào", "hôm nay ra sao", "hiện tại thế nào", "bây giờ thế nào", "tình hình hôm nay")),
            ("WEATHER", ("thời tiết", "có mưa không", "mưa không", "nhiệt độ", "gió", "bão", "dự báo")),
        )
        for intent,markers in rules:
            if intent in intents and any(m in q for m in markers):
                return intent
        # Explicit knowledge subjects outrank incidental destination/weather context.
        subject_rules=(
            ("HISTORY", ("lịch sử", "triều đại", "vua", "chiến tranh")),
            ("CULTURE", ("văn hóa", "phong tục", "truyền thống", "tập quán")),
            ("FOOD", ("ẩm thực", "đặc sản", "món ăn", "ăn gì")),
            ("GUIDE_SCRIPT", ("thuyết minh", "nói với khách", "bài thuyết minh", "kịch bản")),
            ("ACCOMMODATION", ("khách sạn", "lưu trú", "homestay", "resort", "nghỉ ở đâu")),
            ("PRICE", ("giá bao nhiêu", "chi phí", "giá vé", "vé bao nhiêu", "ngân sách")),
            ("OPENING_HOURS", ("mở cửa", "đóng cửa", "giờ mở cửa", "giờ tham quan")),
            ("ACCESSIBILITY", ("xe lăn", "người cao tuổi", "trẻ em", "khó đi", "tiếp cận")),
            ("ENTRY", ("visa", "thị thực", "nhập cảnh", "xuất nhập cảnh", "hộ chiếu")),
            ("SERVICE", ("dịch vụ", "đón tiễn", "đặt xe", "đặt tour", "đặt vé")),
            ("TOURISM_MANAGEMENT", ("quy định du lịch", "giấy phép", "quy định tham quan", "hạn chế tham quan")),
            ("CURRENT_EVENTS", ("sự kiện hôm nay", "sự kiện ngày mai", "đang diễn ra", "lịch sự kiện")),
            ("ECONOMY", ("kinh tế", "ngành kinh tế", "thu nhập", "sản xuất", "doanh nghiệp")),
            ("PEOPLE", ("con người", "dân cư", "người dân", "dân số", "cộng đồng", "dân tộc")),
            ("ADMIN", ("hành chính", "địa giới", "đơn vị hành chính", "thuộc vùng", "thuộc tỉnh", "thuộc thành phố")),
            ("RELIGION", ("tôn giáo", "tín ngưỡng", "thờ", "đền", "chùa", "nhà thờ")),
            ("NATURE", ("thiên nhiên", "hệ sinh thái", "địa chất", "rừng", "hang động", "sông", "núi")),
            ("TRANSPORT", ("giao thông", "sân bay", "bến xe", "tàu", "xe", "đường")),
            ("SHOPPING", ("mua sắm", "quà lưu niệm", "chợ", "mua gì")),
            ("FESTIVAL", ("lễ hội", "sự kiện", "festival", "ngày hội")),
            ("SUSTAINABILITY", ("du lịch bền vững", "môi trường", "rác thải", "bảo tồn")),
        )
        for intent,markers in subject_rules:
            if intent in intents and any(m in q for m in markers):
                return intent
        # Explicit destination requests outrank incidental audience context.
        if "DESTINATION" in intents and any(m in q for m in ("có gì", "nổi bật", "điểm đến", "ở đâu")):
            return "DESTINATION"
        # Audience/profile requests win when the user asks what that group should notice/do.
        if "TOURIST_PROFILE" in intents and any(m in q for m in ("khách ấn", "khách hàn", "khách nhật", "khách trung", "khách quốc tế", "khách việt")) and any(m in q for m in ("lưu ý", "quan tâm", "phù hợp", "nên giới thiệu", "nên thuyết minh")):
            return "TOURIST_PROFILE"
        return intents[0] if intents else "GENERAL_QA"

    def resolve_places(self, query: str) -> List[Dict[str, Any]]:
        q = _norm(query)
        found=[]; seen=set()
        # Longest-match registry covers all 34 current province records, tourism hubs
        # and catalogued landmarks while preserving the distinction between a
        # recognized name and a place for which detailed facts are actually curated.
        for item in resolve_known_place(q):
            key=_norm(item.get("name"))
            if key in seen: continue
            seen.add(key)
            found.append(item)
        return found[:8]

    def _query_contract(self, query: str, primary: str, places: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert a natural-language request into a small executable contract.

        The contract is intentionally transparent and deterministic so the engine
        can prove which part of the question it answered and which context it used.
        """
        q = _norm(query)
        requested = []
        markers = {
            "weather": ("thời tiết", "mưa", "nhiệt độ", "gió", "bão", "dự báo"),
            "distance": ("khoảng cách", "quãng đường", "bao lâu", "di chuyển"),
            "history": ("lịch sử", "triều đại", "vua", "chiến tranh"),
            "culture": ("văn hóa", "phong tục", "truyền thống", "di sản"),
            "food": ("ẩm thực", "đặc sản", "món ăn", "ăn gì"),
            "script": ("thuyết minh", "kịch bản", "nói với khách", "giới thiệu"),
            "risk": ("rủi ro", "cảnh báo", "nguy hiểm", "an toàn"),
            "plan_b": ("plan b", "nếu mưa", "phương án dự phòng", "thay thế"),
            "current": ("hôm nay", "hiện tại", "bây giờ", "đang diễn ra"),
        }
        for key, vals in markers.items():
            if any(v in q for v in vals):
                requested.append(key)
        day_refs = sorted(set(int(x) for x in re.findall(r"ngày\s*(\d{1,2})", q)))
        duration = re.search(r"\b(\d{1,2})\s*(?:ngày|days?)\b", q)
        return {
            "primary": primary,
            "requested_dimensions": requested or [primary.lower()],
            "places": [p.get("name") for p in places],
            "place_count": len(places),
            "days_mentioned": day_refs,
            "duration_days": int(duration.group(1)) if duration else None,
            "answer_scope": "requested_only",
            "preserve_all_places": len(places) > 1,
        }

    def _source_class(self, item: Dict[str, Any]) -> str:
        status = str(item.get("status", "VERIFIED")).upper()
        if item.get("source") == "HDVIA Destination Catalog":
            return "CURATED_CATALOG"
        if status == "REFERENCE" or item.get("source_type") == "editorial_reference":
            return "EDITORIAL_REFERENCE"
        if status == "DISCOVERY_SOURCE":
            return "DISCOVERY"
        return "VERIFIED_SOURCE"

    def predict_questions(self, query: str, intents: List[str] | None = None, places: List[Dict[str, Any]] | None = None) -> List[str]:
        intents = intents or self.detect_intents(query)
        places = places or self.resolve_places(query)
        place = " – ".join(p["name"] for p in places[:3]) if places else "điểm đến này"
        out=[]
        for intent in intents:
            for q in FOLLOWUPS.get(intent, []):
                if "này" in q and place:
                    q=q.replace("điểm này", place).replace("nơi này", place).replace("điểm đến này", place)
                out.append(q)
        if not out:
            out=[f"{place} có gì nổi bật?", f"Có câu chuyện nào hay để thuyết minh về {place}?", f"Thời tiết 7 ngày tới tại {place} thế nào?"]
        # Stable dedupe.
        return list(dict.fromkeys(out))[:6]

    def _answer_scope(self, primary: str, places: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """Declare the exact job and data boundaries before synthesis.

        This makes the routing contract explicit: one primary job, optional supporting
        jobs, all recognized places preserved, and no unrelated domain expansion.
        """
        needs = {
            "WEATHER": ["weather_live"], "CURRENT_STATUS": ["weather_live", "alerts_live"],
            "HISTORY": ["knowledge_history"], "CULTURE": ["knowledge_culture"],
            "FOOD": ["knowledge_food", "service_live"], "GUIDE_SCRIPT": ["knowledge", "guide_context"],
            "ROUTE": ["route_engine"], "ITINERARY": ["journey_engine", "route_engine", "weather_live", "alerts_live"],
            "RISK": ["alerts_live", "weather_live", "journey_engine"], "PLAN_B": ["backup_engine", "weather_live", "journey_engine"],
            "TOURIST_PROFILE": ["tourist_profile", "knowledge"], "DESTINATION": ["destination_catalog", "knowledge"],
            "ADMIN": ["admin_registry"], "RELIGION": ["knowledge_religion"], "NATURE": ["knowledge_nature"],
            "SHOPPING": ["knowledge_shopping", "service_live"], "FESTIVAL": ["event_registry", "official_source"],
            "SUSTAINABILITY": ["knowledge_sustainability"], "ACCOMMODATION": ["accommodation_registry", "service_live"],
            "PRICE": ["official_price_or_service_live"], "OPENING_HOURS": ["official_hours_or_service_live"],
            "ACCESSIBILITY": ["destination_accessibility", "service_live"], "ENTRY": ["official_entry_rules"],
            "SERVICE": ["service_registry", "service_live"], "TOURISM_MANAGEMENT": ["official_regulation"],
            "CURRENT_EVENTS": ["event_registry", "official_source"], "ECONOMY": ["knowledge_economy"],
            "PEOPLE": ["knowledge_people"], "TRANSPORT": ["transport_registry", "transport_live"],
        }.get(primary, ["knowledge_search"])
        return {
            "primary_job": primary,
            "places": [p.get("name") for p in places],
            "place_count": len(places),
            "data_needs": needs,
            "response_rule": "answer_only_requested_scope",
            "no_unrelated_expansion": True,
        }

    def answer(self, query: str, *, journey: Dict[str, Any] | None = None) -> Dict[str, Any]:
        q=(query or "").strip()
        qn=_norm(q)
        intents=self.detect_intents(q)
        places=self.resolve_places(q)
        primary=self._primary_intent(q, intents)
        scope=self._answer_scope(primary, places, q)
        # Primary intent is selected by the evidence-ranked router above.
        lines=[]; sources=[]; confidence="LOW"
        data_status="UNKNOWN"

        # Route questions without a Journey context can still be useful when two
        # curated places have coordinates. This is deliberately labelled ESTIMATE
        # because it is straight-line distance, not live road routing or traffic.
        if primary == "ROUTE" and len(places) >= 2:
            a, b = places[0], places[1]
            ac = a.get("catalog") or a; bc = b.get("catalog") or b
            if ac.get("lat") is not None and ac.get("lon") is not None and bc.get("lat") is not None and bc.get("lon") is not None:
                km = haversine_km(ac, bc)
                lines.append(f"Ước tính khoảng cách đường chim bay giữa {a['name']} và {b['name']} là {km:.0f} km.")
                lines.append("Đây là ESTIMATE, không phải thời gian/ khoảng cách đường bộ LIVE. Muốn tính thời gian di chuyển cần dùng tuyến đường thực tế và tình trạng giao thông.")
                confidence="MEDIUM"; data_status="ESTIMATE"; sources.append("HDVIA Geo Estimate")
        elif primary == "PLAN_B" and not journey:
            if places:
                lines.append(f"HDVIA đã xác định yêu cầu Plan B cho {places[0]['name']}, nhưng chưa có dữ liệu thời tiết/lịch trình LIVE đi kèm để chọn một phương án thay thế cụ thể.")
                lines.append("Không tự bịa điểm thay thế. Khi có lịch trình và thời tiết, HDVIA sẽ đối chiếu các điểm phù hợp, thời gian di chuyển và mức rủi ro trước khi đề xuất.")
                confidence="MEDIUM"; data_status="UNKNOWN"; sources.append("HDVIA Plan B Safety Guard")
        elif primary == "TOURIST_PROFILE" and not journey:
            profile_terms = [x for x in ("khách Ấn Độ", "khách Hàn", "khách Nhật", "khách Trung Quốc", "khách quốc tế") if x in qn]
            profile_name = profile_terms[0] if profile_terms else "nhóm khách này"
            if places:
                lines.append(f"HDVIA nhận diện nhóm khách {profile_name} và điểm đến {places[0]['name']}, nhưng chưa có hồ sơ khách đã kiểm duyệt đủ sâu để đưa ra khuyến nghị đặc thù.")
                lines.append("Hệ thống không suy diễn khẩu vị, tôn giáo hoặc hành vi của khách chỉ từ quốc tịch; cần hồ sơ đoàn cụ thể hoặc nguồn đã kiểm chứng.")
                confidence="MEDIUM"; data_status="UNKNOWN"; sources.append("HDVIA Tourist Profile Safety Guard")

        if journey:
            if primary == "CURRENT_STATUS" and journey.get("weather"):
                status_lines=[]
                for place, forecast in journey["weather"].items():
                    first=next((d for d in forecast if isinstance(d,dict)), None)
                    if not first:
                        continue
                    condition=first.get("condition") or "Chưa có dữ liệu"
                    temp=[]
                    if isinstance(first.get("tmin"),(int,float)): temp.append(f"thấp {first['tmin']:.0f}°C")
                    if isinstance(first.get("tmax"),(int,float)): temp.append(f"cao {first['tmax']:.0f}°C")
                    rain=first.get("rain")
                    rain_text=f", xác suất mưa {rain}%" if isinstance(rain,(int,float)) else ""
                    status_lines.append(f"{place}: {condition}{', ' + ', '.join(temp) if temp else ''}{rain_text}.")
                if status_lines:
                    lines.append("Tình hình hôm nay:")
                    lines.extend(status_lines)
                    if journey.get("risks"):
                        lines.append("Cảnh báo: " + "; ".join(f"{r.get('place')}: {r.get('level')}" for r in journey["risks"][:4]) + ".")
                    confidence="HIGH"; data_status="LIVE"; sources.append("Journey Intelligence / Weather")
            elif primary == "WEATHER" and journey.get("weather"):
                weather_lines=[]
                for place, forecast in journey["weather"].items():
                    valid=[d for d in forecast if isinstance(d, dict)]
                    rain_values=[d.get("rain") for d in valid if d.get("rain") is not None]
                    if rain_values:
                        max_rain=max(rain_values)
                        weather_lines.append(f"{place}: xác suất mưa cao nhất trong 7 ngày là khoảng {max_rain}%." )
                    else:
                        # Weather data may be present but temporarily degraded.
                        # Never fall through to Destination Catalog for a weather question.
                        conditions=[str(d.get("condition")) for d in valid if d.get("condition") and d.get("condition") != "Chưa có dữ liệu"]
                        tmins=[d.get("tmin") for d in valid if isinstance(d.get("tmin"), (int,float))]
                        tmaxs=[d.get("tmax") for d in valid if isinstance(d.get("tmax"), (int,float))]
                        if conditions:
                            weather_lines.append(f"{place}: dữ liệu thời tiết 7 ngày đã được nhận diện; điều kiện dự báo gồm {', '.join(dict.fromkeys(conditions[:4]))}." )
                        if tmins and tmaxs:
                            weather_lines.append(f"Nhiệt độ dự báo khoảng {min(tmins):.0f}–{max(tmaxs):.0f}°C trong các ngày có dữ liệu.")
                if weather_lines:
                    lines.extend(weather_lines)
                    lines.insert(0,"HDVIA đã dùng dữ liệu thời tiết của chính hành trình để trả lời:")
                    confidence="HIGH"; data_status="LIVE"
                    sources.append("Journey Intelligence / Weather")
                else:
                    lines.append("HDVIA đã nhận diện đúng yêu cầu thời tiết nhưng nguồn thời tiết hiện chưa trả về dữ liệu đủ tin cậy. Không dùng dữ liệu điểm đến để thay thế câu trả lời thời tiết.")
                    confidence="LOW"; data_status="UNKNOWN"
                    sources.append("HDVIA Weather Data Boundary")
            if primary in ("RISK","PLAN_B","ITINERARY","ROUTE"):
                if primary == "ITINERARY":
                    total_days=len(journey.get("days") or [])
                    places_all=[p.get("name") for p in journey.get("places") or [] if isinstance(p,dict) and p.get("name")]
                    lines.append(f"Phân tích hành trình: {total_days} ngày/chặng, {len(places_all)} điểm được nhận diện.")
                    if places_all:
                        lines.append("Chuỗi điểm: " + " → ".join(places_all) + ".")
                    quality=journey.get("quality") or {}
                    score=quality.get("score")
                    if isinstance(score,(int,float)):
                        lines.append(f"Điểm chất lượng hiện tại: {score}/100.")
                    issues=[f.get("message") for f in (journey.get("validation") or []) if f.get("severity") in ("HIGH","MEDIUM") and f.get("message")]
                    if issues:
                        lines.append("Cần chú ý: " + " | ".join(issues[:3]))
                    recs=[r for r in (journey.get("recommendations") or []) if r]
                    if recs:
                        lines.append("Đề xuất: " + " | ".join(recs[:3]))
                elif journey.get("risks"):
                    lines.append("Các điểm cần chú ý: " + "; ".join(f"{r.get('place')}: {r.get('level')}" for r in journey["risks"][:4]) + ".")
                if primary in ("PLAN_B","RISK") and journey.get("plan_b"):
                    lines.append("HDVIA đã tạo phương án dự phòng theo ngày trong phần Dự phòng của kết quả phân tích.")
                if primary in ("RISK","PLAN_B","ROUTE") and journey.get("days"):
                    lines.append(f"Lịch trình hiện có {len(journey['days'])} ngày/chặng được nhận diện.")
                if lines:
                    confidence="HIGH"; data_status="LIVE"; sources.append("Journey Intelligence")

        if primary == "WEATHER" and not journey:
            lines.append("HDVIA đã nhận diện đúng câu hỏi thời tiết nhưng chưa có dữ liệu thời tiết LIVE trong ngữ cảnh hiện tại. Không dùng mô tả điểm đến để thay thế dữ liệu thời tiết.")
            confidence="LOW"; data_status="UNKNOWN"
            sources.append("HDVIA Weather Data Boundary")

        if primary == "KNOWLEDGE_GAP":
            # A request for an official/authoritative source is a provenance
            # question, not a request to recycle ordinary destination prose.
            hits=search_knowledge(q, limit=6)
            if places:
                place_names={_norm(p.get("name")) for p in places}
                hits=[h for h in hits if _norm(h.get("destination")) in place_names]
            if hits and places:
                labels=[h.get("source") or h.get("title") for h in hits]
                labels=list(dict.fromkeys(x for x in labels if x))
                lines.append("HDVIA có các nhãn nguồn/tri thức liên quan sau: " + "; ".join(labels[:3]) + ".")
                lines.append("Đây chưa phải xác nhận rằng các nhãn trên là cơ quan phát hành chính thức. Muốn khẳng định tính chính thống cần nguồn gốc/URL hoặc registry nguồn tương ứng.")
                confidence="MEDIUM"; data_status="UNKNOWN"; sources.extend(labels[:3])
            elif places:
                lines.append(f"HDVIA nhận diện {places[0]['name']} nhưng chưa có registry nguồn chính thức đủ dữ liệu để xác nhận URL/cơ quan phát hành cho câu hỏi này.")
                lines.append("Không tự gắn nhãn một nguồn bất kỳ thành nguồn chính thức.")
                confidence="LOW"; data_status="UNKNOWN"; sources.append("HDVIA Source Registry")

        # Additional tourism domains: keep the answer scoped and never substitute generic destination prose.
        if primary in ("ACCOMMODATION", "PRICE", "OPENING_HOURS", "ACCESSIBILITY", "ENTRY", "SERVICE", "TOURISM_MANAGEMENT", "CURRENT_EVENTS") and places and not lines:
            labels={
                "ACCOMMODATION":"lưu trú", "PRICE":"giá/chi phí", "OPENING_HOURS":"giờ mở cửa", "ACCESSIBILITY":"khả năng tiếp cận",
                "ENTRY":"nhập cảnh/giấy tờ", "SERVICE":"dịch vụ", "TOURISM_MANAGEMENT":"quy định du lịch", "CURRENT_EVENTS":"sự kiện"
            }
            lines.append(f"HDVIA đã nhận diện yêu cầu {labels[primary]} cho {', '.join(p['name'] for p in places)}.")
            lines.append("Chức năng đã được định tuyến đúng, nhưng câu trả lời chi tiết chỉ được đưa ra khi có dữ liệu kiểm duyệt hoặc nguồn LIVE phù hợp. HDVIA không tự suy đoán giá, giờ mở cửa, quy định, dịch vụ hay lịch sự kiện.")
            confidence="LOW"; data_status="UNKNOWN"; sources.append("HDVIA Domain Boundary")
        elif primary in ("ACCOMMODATION", "PRICE", "OPENING_HOURS", "ACCESSIBILITY", "ENTRY", "SERVICE", "TOURISM_MANAGEMENT", "CURRENT_EVENTS") and not lines:
            lines.append("HDVIA đã nhận diện đúng lĩnh vực yêu cầu nhưng chưa xác định được địa điểm cụ thể. Hãy nêu tên điểm/tỉnh/thành để hệ thống gọi đúng kho dữ liệu.")
            confidence="LOW"; data_status="UNKNOWN"; sources.append("HDVIA Routing Boundary")

        # Additional tourism domains: use only curated fields or explicitly expose a knowledge boundary.
        if primary == "ADMIN" and places:
            p=places[0]
            lines.append(f"{p['name']} được HDVIA nhận diện thuộc {p.get('province', p.get('region',''))} và vùng {p.get('region','')}.")
            lines.append("Đây là thông tin nhận diện/coverage; các thay đổi hành chính cần được xác minh theo dữ liệu chính thức mới nhất trước khi thuyết minh.")
            confidence="MEDIUM"; data_status="VERIFIED"; sources.append("HDVIA Coverage Registry")
        elif primary in ("ECONOMY","PEOPLE","TRANSPORT","FESTIVAL","SUSTAINABILITY") and places:
            lines.append(f"HDVIA đã nhận diện {places[0]['name']}, nhưng Kho tri thức hiện tại chưa có đủ dữ liệu kiểm duyệt cho câu hỏi {primary.lower()} này.")
            lines.append("Không tự suy đoán số liệu, lịch tổ chức, tình hình giao thông hoặc thông tin kinh tế/xã hội. Cần bổ sung nguồn chuyên ngành hoặc dữ liệu LIVE phù hợp.")
            confidence="LOW"; data_status="UNKNOWN"; sources.append("HDVIA Knowledge Boundary")
        elif primary in ("PEOPLE","RELIGION","NATURE","SHOPPING") and places and places[0].get("catalog"):
            d=places[0]["catalog"]
            detail=(d.get("culture","") if primary in ("PEOPLE","RELIGION") else d.get("overview","") if primary=="NATURE" else d.get("food",""))
            if detail:
                lines.append(f"{d['name']}: {detail}")
                lines.append("Lưu ý: đây là mô tả trong catalog; thông tin định lượng, giá, giờ mở cửa hoặc tình trạng hiện tại cần nguồn LIVE/nguồn chính thức.")
                confidence="MEDIUM"; data_status="VERIFIED"; sources.append("HDVIA Destination Catalog")

        hits=search_knowledge(q, limit=5, intent=primary)
        if places:
            place_names={_norm(p.get("name")) for p in places}
            hits=[h for h in hits if _norm(h.get("destination")) in place_names or any(_norm(p.get("name")) in _norm(h.get("content","")) for p in places)]
        if hits and primary not in ("WEATHER", "CURRENT_STATUS", "ROUTE", "RISK", "PLAN_B", "TOURIST_PROFILE", "KNOWLEDGE_GAP", "GENERAL_QA") and not _requires_verified_detail(q, primary):
            verified = [h for h in hits if self._source_class(h) in ("CURATED_CATALOG", "VERIFIED_SOURCE")]
            reference = [h for h in hits if self._source_class(h) in ("EDITORIAL_REFERENCE", "DISCOVERY")]
            if verified:
                lines.append("Theo tri thức đã được HDVIA đăng ký/kiểm duyệt:")
            elif reference:
                lines.append("Theo nguồn tham khảo du lịch được HDVIA liên kết:")
            for item in hits:
                catalog=item.get("catalog") or {}
                if primary == "HISTORY" and catalog.get("history"):
                    detail=catalog["history"]
                elif primary == "CULTURE" and catalog.get("culture"):
                    detail=catalog["culture"]
                elif primary == "FOOD" and catalog.get("food"):
                    detail=catalog["food"]
                elif primary in ("DESTINATION","GUIDE_SCRIPT","GENERAL_QA") and catalog.get("overview"):
                    detail=catalog["overview"]
                else:
                    detail=item.get("summary", "")
                lines.append(f"• {item['title']}: {detail}")
                if catalog.get("highlights") and primary in ("DESTINATION","GUIDE_SCRIPT"):
                    lines.append("  Điểm nổi bật: " + ", ".join(catalog["highlights"][:5]) + ".")
                src = item.get("source") or item.get("title", "Kho tri thức")
                sources.append(src)
                if self._source_class(item) in ("EDITORIAL_REFERENCE", "DISCOVERY"):
                    lines.append("  Trạng thái nguồn: tham khảo/khám phá; cần đối chiếu nguồn chính thức nếu dùng cho thông tin hiện tại hoặc chi tiết định lượng.")
            confidence="HIGH" if any(self._source_class(item) == "CURATED_CATALOG" for item in hits) else ("MEDIUM" if len(hits)>=2 else "LOW")
            data_status="VERIFIED" if any(self._source_class(item) == "CURATED_CATALOG" for item in hits) else "REFERENCE"

        # Self-healing knowledge loop: when the curated warehouse is sparse,
        # HDVIA automatically acquires reference evidence for the detected place
        # and uses it in this answer immediately. It never promotes it to
        # VERIFIED/PUBLISHED automatically.
        auto_heal = os.environ.get("HDVIA_AUTO_KNOWLEDGE_ENRICH", "1").strip().lower() in {"1", "true", "yes", "on"}
        self_heal = None
        if auto_heal and places and primary in ("HISTORY", "CULTURE", "FOOD", "GUIDE_SCRIPT", "DESTINATION", "GENERAL_QA", "NATURE", "PEOPLE", "ECONOMY", "FESTIVAL", "SHOPPING", "RELIGION") and not _requires_verified_detail(q, primary):
            try:
                target_place = places[0].get("name") or ""
                self_heal = KnowledgeSelfHealingEngine().ensure(target_place, question=q, domain=primary)
                if self_heal.get("ok"):
                    acquired_lines = reference_lines(self_heal.get("profile") or {}, domain=primary)
                    if acquired_lines:
                        lines.append("HDVIA vừa tự bổ sung dữ liệu tham khảo cho điểm đến:")
                        lines.extend(acquired_lines)
                        sources.append("HDVIA Smart Knowledge Acquisition")
                        if self_heal.get("status") == "ACQUIRED":
                            data_status = "REFERENCE"
                            confidence = "MEDIUM" if confidence == "LOW" else confidence
            except Exception:
                self_heal = None

        if not lines and places and primary in ("HISTORY", "CULTURE", "FOOD", "GUIDE_SCRIPT", "DESTINATION", "GENERAL_QA") and not _requires_verified_detail(q, primary):
            # Preserve every resolved place in a multi-destination question.
            answered=0
            for place in places:
                d=place.get("catalog") or {}
                if not d:
                    continue
                if primary == "FOOD":
                    detail=d.get('food','Chưa có dữ liệu ẩm thực trong catalog.')
                elif primary == "HISTORY":
                    detail=d.get('history','Chưa có dữ liệu lịch sử trong catalog.')
                elif primary == "CULTURE":
                    detail=d.get('culture','Chưa có dữ liệu văn hóa trong catalog.')
                else:
                    detail=d.get('overview','')
                if detail:
                    lines.append(f"{d.get('name', place.get('name'))}: {detail}")
                    if d.get('highlights') and primary in ("GUIDE_SCRIPT", "DESTINATION"):
                        lines.append("  Điểm nổi bật: " + ", ".join(d['highlights'][:4]) + ".")
                    answered += 1
            if answered:
                confidence="MEDIUM"; data_status="VERIFIED"; sources.append("HDVIA Destination Catalog")

        if not lines:
            if places:
                p=places[0]
                lines.append(f"HDVIA đã nhận diện {p['name']} thuộc {p.get('province','')} ({p.get('region','')}).")
                lines.append("Tên địa điểm đã được nhận diện, nhưng HDVIA chưa có đủ tri thức đã kiểm duyệt để khẳng định chi tiết cho câu hỏi này; hệ thống không tự bịa thông tin.")
                lines.append("Có thể tiếp tục bằng cách hỏi về lịch sử, văn hóa, ẩm thực, thuyết minh, thời tiết hoặc Plan B của chính địa điểm này.")
                confidence="MEDIUM"
                data_status="UNKNOWN"
                sources.append("HDVIA Coverage Registry")
            else:
                lines.append("HDVIA đã hiểu câu hỏi nhưng chưa có nguồn dữ liệu đủ tin cậy để trả lời trực tiếp. Hãy thêm tên địa điểm, thời gian hoặc tình huống cụ thể để hệ thống phân tích chính xác hơn.")
                confidence="LOW"
                data_status="UNKNOWN"

        enrichment = None
        if (self.external_enricher and os.environ.get("HDVIA_AI_AUTO_ENRICH", "0") == "1"
                and primary not in ("WEATHER", "CURRENT_STATUS", "ROUTE", "RISK", "PLAN_B", "ITINERARY")
                and (not lines or confidence == "LOW" or data_status == "UNKNOWN")):
            try:
                place = " – ".join(p.get("name", "") for p in places[:3])
                enrichment = self.external_enricher(question=q, place=place, domain=primary)
                if enrichment and enrichment.get("ok"):
                    candidate = enrichment.get("candidate") or {}
                    if str(candidate.get("content") or "").strip():
                        lines.append("AI Connect đã tìm thấy dữ liệu bổ sung ở chế độ kiểm chứng; dữ liệu này chưa được xem là tri thức đã xác minh.")
                        sources.append("HDVIA AI Connect – Candidate")
                        data_status = "CANDIDATE"
                        confidence = "MEDIUM"
            except Exception:
                enrichment = None

        return {
            "ok": True,
            "engine": self.VERSION,
            "query_contract": self._query_contract(q, primary, places),
            "query": q,
            "intent": primary,
            "intents": intents,
            "places": places,
            "answer": "\n".join(lines),
            "confidence": confidence,
            "data_status": data_status,
            "sources": list(dict.fromkeys(sources))[:6],
            "predicted_questions": self.predict_questions(q, intents, places),
            "routing": scope,
            "knowledge_enrichment": enrichment,
            "self_healing": self_heal,
            "coverage": {"categories": CATEGORIES, "recognized_place_count": len(places),

                         "knowledge_mode": "verified-first; editorial reference is labeled and unknown facts are surfaced instead of invented",
                         "retrieval": "intent-aware multi-signal ranking",
                         "point_intelligence": "enabled"},
        }
