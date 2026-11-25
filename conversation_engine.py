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
        for p in PROVINCES_2025:
            names=[p.get("name"), *(p.get("aliases") or []), *(p.get("tourism_hubs") or [])]
            for name in names:
                n=_norm(name)
                if n and n in q and n not in seen:
                    catalog=next((d for d in DESTINATIONS if d.get("slug")==p.get("slug") or _norm(d.get("name"))==_norm(name)), None)
                    found.append({"name": name, "province": p.get("name"), "region": p.get("region"), "slug": p.get("slug"), "kind":"province", "catalog":catalog})
                    seen.add(n)
                    break
        for d in DESTINATIONS:
            names=[d.get("name"), *(d.get("highlights") or [])]
            for name in names:
                n=_norm(name)
                if n and n in q and n not in seen:
                    found.append({"name": name, "province": d.get("name"), "region": d.get("region"), "slug": d.get("slug"), "kind":"destination", "catalog":d})
                    seen.add(n)
                    break
        return found[:6]

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
            lines.append("Theo Kho tri thức HDVIA:")
            for item in hits:
                lines.append(f"• {item['title']}: {item['summary']}")
                sources.append(item.get("title", "Kho tri thức"))
            confidence="HIGH" if len(hits)>=2 else "MEDIUM"

        if not lines and places and places[0].get("catalog"):
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
                lines.append(f"HDVIA đã nhận diện {p['name']} thuộc {p['province']} ({p['region']}).")
                lines.append("Hiện dữ liệu tri thức đã kiểm duyệt cho truy vấn này chưa đủ để khẳng định thêm thông tin cụ thể. Sếp có thể chọn một câu hỏi gợi ý bên dưới để HDVIA phân tích tiếp.")
                confidence="MEDIUM"
                sources.append("Province Data 2025")
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
        }
