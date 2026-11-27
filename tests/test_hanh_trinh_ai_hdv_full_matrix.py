"""HDV real-world question matrix for Hành Trình AI.

This is a routing/coverage regression suite, not a claim that every fact is already
curated. Every question must be routed to a named tourism function and preserve the
recognized place. Unknown facts must surface a data boundary rather than hallucinate.
"""
from conversation_engine import ConversationIntelligenceEngine
from province_data import PROVINCES_2025

DOMAINS = {
    "WEATHER": "{p} hôm nay thời tiết thế nào?",
    "HISTORY": "Lịch sử {p} có gì HDV cần biết?",
    "CULTURE": "Văn hóa {p} có gì đáng giới thiệu?",
    "FOOD": "{p} có đặc sản gì?",
    "GUIDE_SCRIPT": "Thuyết minh {p} cho khách như thế nào?",
    "ROUTE": "Từ {p} đi điểm khác cần lưu ý gì về lộ trình?",
    "ITINERARY": "Phân tích hành trình qua {p}.",
    "RISK": "{p} có rủi ro nào HDV cần lưu ý?",
    "PLAN_B": "Nếu {p} mưa thì Plan B là gì?",
    "TOURIST_PROFILE": "Khách quốc tế đến {p} cần lưu ý gì?",
    "DESTINATION": "{p} có gì nổi bật?",
    "ECONOMY": "Kinh tế {p} có gì đáng giới thiệu cho khách?",
    "PEOPLE": "Con người và cộng đồng ở {p} có gì cần biết?",
    "ADMIN": "{p} hiện thuộc đơn vị hành chính nào?",
    "RELIGION": "Tín ngưỡng và tôn giáo ở {p} có gì đáng chú ý?",
    "NATURE": "Thiên nhiên ở {p} có gì nổi bật?",
    "TRANSPORT": "Giao thông đến {p} nên đi thế nào?",
    "SHOPPING": "Ở {p} nên mua gì làm quà?",
    "FESTIVAL": "{p} có lễ hội hoặc sự kiện gì?",
    "SUSTAINABILITY": "Du lịch bền vững ở {p} cần lưu ý gì?",
    "ACCOMMODATION": "Ở {p} nên tìm lưu trú thế nào?",
    "PRICE": "Chi phí/giá vé ở {p} cần kiểm tra gì?",
    "OPENING_HOURS": "{p} mở cửa giờ nào?",
    "ACCESSIBILITY": "{p} có phù hợp người cao tuổi hoặc xe lăn không?",
    "ENTRY": "Đến {p} có giấy tờ hoặc quy định nhập cảnh nào cần lưu ý?",
    "SERVICE": "Ở {p} cần đặt trước dịch vụ nào?",
    "TOURISM_MANAGEMENT": "Quy định tham quan ở {p} cần lưu ý gì?",
    "CURRENT_EVENTS": "{p} hôm nay có sự kiện gì đang diễn ra?",
}


def test_all_34_provinces_are_routable_across_all_hdv_domains():
    e = ConversationIntelligenceEngine()
    for p in PROVINCES_2025:
        name = p["name"]
        for expected, template in DOMAINS.items():
            r = e.answer(template.format(p=name))
            assert r["ok"] is True
            assert r["places"], (expected, name, r)
            assert r["places"][0]["name"] in name or name in r["places"][0]["name"]
            assert r["intent"] == expected, (expected, name, r["intent"], r["answer"])
            assert r["routing"]["primary_job"] == expected


def test_multi_place_questions_preserve_every_destination():
    e = ConversationIntelligenceEngine()
    queries = [
        "Đà Nẵng, Hội An và Huế ngày mai thời tiết thế nào?",
        "Đà Nẵng - Hội An - Huế có gì nổi bật?",
        "Phân tích hành trình Hà Nội - Ninh Bình - Hạ Long - Hải Phòng 5 ngày.",
        "Nếu Đà Nẵng, Hội An và Huế đều có mưa thì Plan B thế nào?",
    ]
    for q in queries:
        r = e.answer(q)
        assert r["ok"] is True
        assert r["routing"]["place_count"] >= 3


def test_unknown_fact_stays_scoped_instead_of_becoming_generic_destination_prose():
    e = ConversationIntelligenceEngine()
    r = e.answer("Bản Giốc giá vé chính xác hôm nay là bao nhiêu?")
    assert r["intent"] == "PRICE"
    assert "không" in r["answer"].lower() or "chưa" in r["answer"].lower()
    assert "Bản Giốc" in r["answer"]
