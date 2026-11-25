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
from journey_engine.engine import haversine_km

INTENTS = {
    "WEATHER": ("thời tiết", "mưa", "nhiệt độ", "nắng", "gió", "bão", "dông", "weather"),
    "HISTORY": ("lịch sử", "lịch sử hình thành", "vua", "triều đại", "chiến tranh"),
    "CULTURE": ("văn hóa", "phong tục", "truyền thống", "tập quán", "di sản"),
    "FOOD": ("ẩm thực", "món ăn", "đặc sản", "ăn gì", "quán ăn", "nhà hàng"),
    "GUIDE_SCRIPT": ("thuyết minh", "giới thiệu", "nói với khách", "bài thuyết minh", "kịch bản"),
    "ROUTE": ("lộ trình", "đi bao lâu", "mất bao lâu", "bao lâu để đi", "khoảng cách", "quãng đường", "di chuyển", "tuyến"),
    "ITINERARY": ("ngày 1", "ngày 2", "ngày 3", "ngày 4", "ngày 5", "lịch trình", "tour", "hành trình"),
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
        # Resolve action-oriented questions before broad context intents.
        # A conditional request such as "nếu mưa thì đổi lịch thế nào" is
        # operationally a PLAN_B request, even though WEATHER is also present.
        qn=_norm(q)
        if "PLAN_B" in intents and any(x in qn for x in ("nếu mưa", "nếu trời mưa", "plan b", "phương án dự phòng", "phương án thay thế")):
            primary="PLAN_B"
        elif "KNOWLEDGE_GAP" in intents and any(x in qn for x in ("nguồn chính thức", "có nguồn không", "kiểm chứng", "theo nguồn")):
            primary="KNOWLEDGE_GAP"
        elif "TOURIST_PROFILE" in intents and any(x in qn for x in ("khách ấn", "khách hàn", "khách nhật", "khách trung", "khách việt", "khách lớn tuổi", "trẻ em")):
            primary="TOURIST_PROFILE"
        elif "TOURIST_PROFILE" in intents and "khách quốc tế" in qn and any(x in qn for x in ("cần lưu ý", "quan tâm", "phù hợp", "nên giới thiệu", "nên thuyết minh")):
            primary="TOURIST_PROFILE"
        elif "ROUTE" in intents and any(x in qn for x in ("mất bao lâu", "bao lâu để đi", "khoảng cách", "quãng đường")):
            primary="ROUTE"
        elif "RISK" in intents and any(x in qn for x in ("nguy hiểm", "an toàn", "cảnh báo", "rủi ro")):
            primary="RISK"
        else:
            # Prefer the explicit subject of the question over incidental context
            # such as "trong mùa mưa" or "cho khách quốc tế".
            lead_priority=("HISTORY", "CULTURE", "FOOD", "GUIDE_SCRIPT", "WEATHER", "ITINERARY", "ROUTE", "RISK", "ECONOMY", "PEOPLE", "ADMIN", "RELIGION", "NATURE", "TRANSPORT", "SHOPPING", "FESTIVAL", "SUSTAINABILITY", "EXPERIENCE", "DESTINATION")
            lead_text=_norm(q.split("?", 1)[0])
            for candidate in lead_priority:
                if candidate in intents:
                    markers={
                        "HISTORY": ("lịch sử",), "CULTURE": ("văn hóa",),
                        "FOOD": ("ẩm thực", "đặc sản", "món ăn", "ăn gì"),
                        "GUIDE_SCRIPT": ("thuyết minh", "giới thiệu", "nói với khách", "bài thuyết minh", "kịch bản"),
                        "WEATHER": ("thời tiết", "nhiệt độ", "gió", "bão", "dông"),
                        "ITINERARY": ("lịch trình", "hành trình", "tour", "ngày 1", "ngày 2"),
                        "EXPERIENCE": ("kinh nghiệm", "mẹo", "lưu ý", "nên làm gì", "gợi ý"),
                        "DESTINATION": ("có gì", "nổi tiếng", "điểm đến", "ở đâu"),
                        "ECONOMY": ("kinh tế", "ngành kinh tế", "thu nhập", "sản xuất", "doanh nghiệp"),
                        "PEOPLE": ("dân cư", "người dân", "dân số", "cộng đồng", "dân tộc"),
                        "ADMIN": ("tỉnh", "thành phố", "hành chính", "địa giới", "đơn vị hành chính", "thuộc vùng", "vùng nào"),
                        "RELIGION": ("tôn giáo", "tín ngưỡng", "thờ", "đền", "chùa", "nhà thờ"),
                        "NATURE": ("thiên nhiên", "hệ sinh thái", "địa chất", "rừng", "hang động", "sông", "núi"),
                        "TRANSPORT": ("giao thông", "sân bay", "bến xe", "tàu", "xe", "đường"),
                        "SHOPPING": ("mua sắm", "đặc sản mua", "quà", "quà lưu niệm", "chợ", "mua"),
                        "FESTIVAL": ("lễ hội", "sự kiện", "festival", "ngày hội"),
                        "SUSTAINABILITY": ("du lịch bền vững", "môi trường", "rác thải", "bảo tồn"),
                    }[candidate]
                    if any(m in lead_text for m in markers):
                        primary=candidate; break
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
            if primary == "WEATHER" and journey.get("weather"):
                for place, forecast in journey["weather"].items():
                    valid=[d for d in forecast if d.get("rain") is not None]
                    if valid:
                        max_rain=max(d.get("rain") or 0 for d in valid)
                        lines.append(f"{place}: xác suất mưa cao nhất trong 7 ngày là khoảng {max_rain}%." )
                if lines:
                    lines.insert(0,"HDVIA đã dùng dữ liệu thời tiết của chính hành trình để trả lời:")
                    confidence="HIGH"; data_status="LIVE"
                    sources.append("Journey Intelligence / Weather")
            if primary in ("RISK","PLAN_B","ITINERARY","ROUTE"):
                if journey.get("risks"):
                    lines.append("Các điểm cần chú ý: " + "; ".join(f"{r.get('place')}: {r.get('level')}" for r in journey["risks"][:4]) + ".")
                if primary in ("PLAN_B","RISK") and journey.get("plan_b"):
                    lines.append("HDVIA đã tạo phương án dự phòng theo ngày trong phần Dự phòng của kết quả phân tích.")
                if journey.get("days"):
                    lines.append(f"Lịch trình hiện có {len(journey['days'])} ngày/chặng được nhận diện.")
                if lines:
                    confidence="HIGH"; data_status="LIVE"; sources.append("Journey Intelligence")

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

        hits=search_knowledge(q, limit=3)
        if places:
            place_names={_norm(p.get("name")) for p in places}
            hits=[h for h in hits if _norm(h.get("destination")) in place_names or any(_norm(p.get("name")) in _norm(h.get("content","")) for p in places)]
        if hits and primary not in ("WEATHER", "ROUTE", "RISK", "PLAN_B", "TOURIST_PROFILE", "KNOWLEDGE_GAP", "GENERAL_QA"):
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
            data_status="VERIFIED"

        if not lines and places and places[0].get("catalog") and primary in ("HISTORY", "CULTURE", "FOOD", "GUIDE_SCRIPT", "DESTINATION", "GENERAL_QA") and not _requires_verified_detail(q, primary):
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

        return {
            "ok": True,
            "engine": self.VERSION,
            "query": q,
            "intent": primary,
            "intents": intents,
            "places": places,
            "answer": "\n".join(lines),
            "confidence": confidence,
            "data_status": data_status,
            "sources": list(dict.fromkeys(sources))[:6],
            "predicted_questions": self.predict_questions(q, intents, places),
            "coverage": {"categories": CATEGORIES, "recognized_place_count": len(places),
                         "knowledge_mode": "verified-only; unknown facts are surfaced instead of invented"},
        }
