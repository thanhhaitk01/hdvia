"""HDVIA Conversation Intelligence Layer.

Deterministic, provider-neutral conversation understanding for Beta releases.
It does not invent facts: answers are synthesized from the curated knowledge
layer and live Journey Intelligence context, while unknowns are surfaced as such.
"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Tuple

from knowledge_layer import search_knowledge
from province_data import PROVINCES_2025
from destination_catalog import DESTINATIONS
from coverage_registry import CATEGORIES, resolve_known_place

INTENTS = {
    "WEATHER": ("thời tiết", "mưa", "nhiệt độ", "nắng", "gió", "bão", "dông", "weather"),
    "HISTORY": ("lịch sử", "lịch sử hình thành", "vua", "triều đại", "chiến tranh"),
    "CULTURE": ("văn hóa", "phong tục", "truyền thống", "tập quán", "di sản"),
    "FOOD": ("ẩm thực", "món ăn", "đặc sản", "ăn gì", "quán ăn", "nhà hàng"),
    "GUIDE_SCRIPT": ("thuyết minh", "giới thiệu", "nói với khách", "bài thuyết minh", "kịch bản"),
    "ROUTE": ("lộ trình", "đi bao lâu", "khoảng cách", "quãng đường", "di chuyển", "tuyến"),
    "ITINERARY": ("ngày 1", "ngày 2", "ngày 3", "ngày 4", "ngày 5", "lịch trình", "tour", "hành trình"),
    "RISK": ("rủi ro", "cảnh báo", "nguy hiểm", "an toàn", "mưa bão", "đường xấu"),
    "PLAN_B": ("plan b", "phương án dự phòng", "thay thế", "nếu trời mưa", "nếu mưa"),
    "TOURIST_PROFILE": ("khách ấn", "khách hàn", "khách nhật", "khách trung", "khách quốc tế", "khách việt", "khách lớn tuổi", "trẻ em"),
    "EXPERIENCE": ("kinh nghiệm", "mẹo", "lưu ý", "nên làm gì", "gợi ý"),
    "DESTINATION": ("ở đâu", "có gì", "nổi tiếng", "điểm đến", "tham quan"),
    "KNOWLEDGE_GAP": ("chưa có dữ liệu", "chưa biết", "có nguồn không", "nguồn chính thức", "kiểm chứng"),
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
    VERSION = "1.0.0-conversation"

    def detect_intents(self, query: str) -> List[str]:
        q = _norm(query)
        found = []
        for intent, terms in INTENTS.items():
            if any(t in q for t in terms):
                found.append(intent)
        if not found:
            found.append("GENERAL_QA")
        # Destination is a useful secondary intent whenever a place is resolved.
        if self.resolve_places(query) and "DESTINATION" not in found and not any(x in found for x in ("ITINERARY", "WEATHER", "ROUTE")):
            found.append("DESTINATION")
        return found[:4]

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

    def predict_questions(self, query: str, intents: List[str] | None = None, places: List[Dict[str, Any]] | None = None) -> List[str]:
        intents = intents or self.detect_intents(query)
        places = places or self.resolve_places(query)
        place = places[0]["name"] if places else "điểm đến này"
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

    def answer(self, query: str, *, journey: Dict[str, Any] | None = None) -> Dict[str, Any]:
        q=(query or "").strip()
        intents=self.detect_intents(q)
        places=self.resolve_places(q)
        primary=intents[0] if intents else "GENERAL_QA"
        lines=[]; sources=[]; confidence="LOW"

        if journey:
            if primary == "WEATHER" and journey.get("weather"):
                for place, forecast in journey["weather"].items():
                    valid=[d for d in forecast if d.get("rain") is not None]
                    if valid:
                        max_rain=max(d.get("rain") or 0 for d in valid)
                        lines.append(f"{place}: xác suất mưa cao nhất trong 7 ngày là khoảng {max_rain}%." )
                if lines:
                    lines.insert(0,"HDVIA đã dùng dữ liệu thời tiết của chính hành trình để trả lời:")
                    confidence="HIGH"
                    sources.append("Journey Intelligence / Weather")
            if primary in ("RISK","PLAN_B","ITINERARY","ROUTE"):
                if journey.get("risks"):
                    lines.append("Các điểm cần chú ý: " + "; ".join(f"{r.get('place')}: {r.get('level')}" for r in journey["risks"][:4]) + ".")
                if primary in ("PLAN_B","RISK") and journey.get("plan_b"):
                    lines.append("HDVIA đã tạo phương án dự phòng theo ngày trong phần Dự phòng của kết quả phân tích.")
                if journey.get("days"):
                    lines.append(f"Lịch trình hiện có {len(journey['days'])} ngày/chặng được nhận diện.")
                if lines:
                    confidence="HIGH"; sources.append("Journey Intelligence")

        hits=search_knowledge(q, limit=3)
        if places:
            place_names={_norm(p.get("name")) for p in places}
            hits=[h for h in hits if _norm(h.get("destination")) in place_names or any(_norm(p.get("name")) in _norm(h.get("content","")) for p in places)]
        if hits and primary not in ("WEATHER", "ROUTE", "RISK", "PLAN_B", "GENERAL_QA"):
            lines.append("Theo dữ liệu du lịch đã được HDVIA kiểm duyệt/đăng ký:")
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
                sources.append(item.get("source") or item.get("title", "Kho tri thức"))
            confidence="HIGH" if any(item.get("source") == "HDVIA Destination Catalog" for item in hits) else ("MEDIUM" if len(hits)>=2 else "LOW")

        if not lines and places and places[0].get("catalog") and not _requires_verified_detail(q, primary):
            d=places[0]["catalog"]
            if primary in ("FOOD",):
                lines.append(f"{d['name']}: {d.get('food','Chưa có dữ liệu ẩm thực trong catalog.')}")
            elif primary in ("HISTORY",):
                lines.append(f"{d['name']}: {d.get('history','Chưa có dữ liệu lịch sử trong catalog.')}")
            elif primary in ("CULTURE",):
                lines.append(f"{d['name']}: {d.get('culture','Chưa có dữ liệu văn hóa trong catalog.')}")
            elif primary in ("GUIDE_SCRIPT", "DESTINATION", "GENERAL_QA"):
                lines.append(f"{d['name']}: {d.get('overview','')}")
                if d.get('highlights'):
                    lines.append("Điểm nổi bật: " + ", ".join(d['highlights'][:4]) + ".")
            lines.append(f"Phù hợp: {d.get('best_for','Chưa có dữ liệu phân nhóm trải nghiệm.')}")
            confidence="MEDIUM"; sources.append("HDVIA Destination Catalog")

        if not lines:
            if places:
                p=places[0]
                lines.append(f"HDVIA đã nhận diện {p['name']} thuộc {p.get('province','')} ({p.get('region','')}).")
                lines.append("Tên địa điểm đã được nhận diện, nhưng HDVIA chưa có đủ tri thức đã kiểm duyệt để khẳng định chi tiết cho câu hỏi này; hệ thống không tự bịa thông tin.")
                lines.append("Có thể tiếp tục bằng cách hỏi về lịch sử, văn hóa, ẩm thực, thuyết minh, thời tiết hoặc Plan B của chính địa điểm này.")
                confidence="MEDIUM"
                sources.append("HDVIA Coverage Registry")
            else:
                lines.append("HDVIA đã hiểu câu hỏi nhưng chưa có nguồn dữ liệu đủ tin cậy để trả lời trực tiếp. Hãy thêm tên địa điểm, thời gian hoặc tình huống cụ thể để hệ thống phân tích chính xác hơn.")
                confidence="LOW"

        return {
            "ok": True,
            "engine": self.VERSION,
            "query": q,
            "intent": primary,
            "intents": intents,
            "places": places,
            "answer": "\n".join(lines),
            "confidence": confidence,
            "sources": list(dict.fromkeys(sources))[:6],
            "predicted_questions": self.predict_questions(q, intents, places),
            "coverage": {"categories": CATEGORIES, "recognized_place_count": len(places),
                         "knowledge_mode": "verified-only; unknown facts are surfaced instead of invented"},
        }
