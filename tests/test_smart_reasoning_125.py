from conversation_engine import ConversationIntelligenceEngine
from knowledge_layer import search_knowledge

def test_query_contract_preserves_multi_place_and_requested_dimensions():
    e=ConversationIntelligenceEngine()
    r=e.answer("Đà Nẵng và Hội An 3 ngày có gì nên thuyết minh và thời tiết thế nào?")
    c=r["query_contract"]
    assert c["preserve_all_places"] is True
    assert c["place_count"] >= 2
    assert "weather" in c["requested_dimensions"]
    assert "script" in c["requested_dimensions"]

def test_editorial_reference_is_not_mislabeled_verified():
    e=ConversationIntelligenceEngine()
    r=e.answer("Cầu ngói Thanh Toàn kiến trúc và thuyết minh")
    assert r["ok"]
    assert r["data_status"] in ("REFERENCE", "VERIFIED")
    if r["data_status"] == "REFERENCE":
        assert "tham khảo" in r["answer"].lower()

def test_intent_aware_search_accepts_intent_without_breaking_api():
    hits=search_knowledge("Thanh Toàn kiến trúc", limit=3, intent="CULTURE")
    assert hits
    assert any("Thanh Toàn" in (h.get("title") or "") for h in hits)

def test_point_question_never_invents_missing_exact_fact():
    e=ConversationIntelligenceEngine()
    r=e.answer("Cầu ngói Thanh Toàn cho tôi con số chính xác chưa có trong dữ liệu")
    assert r["ok"]
    assert "chưa có nguồn" in r["answer"].lower() or "chưa có đủ" in r["answer"].lower()
