"""Real-world HDV question matrix: domain coverage, safe boundaries and regression.
The matrix is deterministic and expands by combining curated destinations with HDV intents.
"""
from conversation_engine import ConversationIntelligenceEngine
from destination_catalog import DESTINATIONS
from province_data import PROVINCES_2025

TEMPLATES = {
    "HISTORY": "Lịch sử của {place} có gì quan trọng để HDV thuyết minh?",
    "CULTURE": "Văn hóa của {place} có gì đáng giới thiệu cho khách?",
    "FOOD": "Ở {place} có đặc sản gì nên giới thiệu?",
    "DESTINATION": "{place} có gì nổi bật đối với khách du lịch?",
    "NATURE": "Giá trị thiên nhiên của {place} là gì?",
    "RELIGION": "Tín ngưỡng hoặc không gian tôn giáo ở {place} có gì cần lưu ý?",
    "PEOPLE": "Cộng đồng và đời sống ở {place} có gì đáng giới thiệu?",
    "ADMIN": "{place} thuộc vùng nào và HDV cần lưu ý gì về thông tin hành chính?",
    "ECONOMY": "Kinh tế ở {place} có gì HDV nên biết?",
    "TRANSPORT": "Giao thông ở {place} có gì cần HDV lưu ý?",
    "SHOPPING": "Ở {place} nên giới thiệu đặc sản hoặc mua sắm gì?",
    "FESTIVAL": "{place} có lễ hội hoặc sự kiện nào HDV nên biết?",
    "SUSTAINABILITY": "HDV cần lưu ý gì về bảo tồn và du lịch bền vững tại {place}?",
}


def test_matrix_domains_are_recognized():
    e = ConversationIntelligenceEngine()
    for place in list(DESTINATIONS) + list(PROVINCES_2025):
        name = place["name"]
        for expected, template in TEMPLATES.items():
            result = e.answer(template.format(place=name))
            assert result["ok"] is True
            assert result["places"], (expected, name, result)
            assert expected in result["intents"] or result["intent"] == expected, (expected, name, result)
            assert result["answer"].strip()


def test_exact_fact_without_verified_support_is_not_fabricated():
    e = ConversationIntelligenceEngine()
    q = "Ai xây dựng địa danh này năm 1234? Hãy cho tôi nguồn chính thức."
    result = e.answer(q)
    assert result["data_status"] == "UNKNOWN"
    assert "không" in result["answer"].lower() or "chưa" in result["answer"].lower()


def test_live_sensitive_domains_are_explicitly_bounded():
    e = ConversationIntelligenceEngine()
    for q in (
        "Tình hình giao thông ở Đà Nẵng hiện nay thế nào?",
        "Lễ hội ở Huế năm nay diễn ra ngày nào?",
        "Kinh tế hiện nay của Huế thế nào?",
    ):
        r=e.answer(q)
        assert r["ok"]
        assert r["data_status"] in ("UNKNOWN", "VERIFIED")
        assert r["answer"].strip()
