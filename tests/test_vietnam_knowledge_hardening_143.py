from conversation_engine import ConversationIntelligenceEngine
from knowledge_layer import search_knowledge


def test_catalog_answers_history_and_culture_for_known_destination():
    e=ConversationIntelligenceEngine()
    r=e.answer("Mỹ Sơn lịch sử và văn hóa có gì để HDV thuyết minh?")
    assert r["places"]
    assert "Mỹ Sơn" in r["answer"]
    assert "chưa có đủ tri thức" not in r["answer"].lower()
    assert r["confidence"] in ("HIGH", "MEDIUM")


def test_all_vietnam_registry_is_retrievable_without_fake_facts():
    samples=["Bản Giốc", "Pác Bó", "Đồng Văn", "Cái Răng", "Phú Quốc", "Hoàng thành Thăng Long"]
    for q in samples:
        hits=search_knowledge(q)
        assert hits, q
        assert any(h.get("source") in ("HDVIA Vietnam Coverage Registry", "HDVIA Destination Catalog") or h.get("id","").startswith("catalog-") or h.get("id","").startswith("province-") for h in hits), q


def test_unknown_detail_does_not_invent():
    e=ConversationIntelligenceEngine()
    r=e.answer("Pác Bó cho tôi con số chi tiết chưa có trong dữ liệu")
    assert r["ok"]
    assert "không" in r["answer"].lower() or "chưa" in r["answer"].lower()
