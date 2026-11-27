from conversation_engine import ConversationIntelligenceEngine


def test_multi_destination_weather_keeps_all_places():
    e = ConversationIntelligenceEngine()
    places = e.resolve_places("Đà Nẵng, Hội An và Huế ngày mai thời tiết thế nào?")
    assert [p["name"] for p in places[:3]] == ["Đà Nẵng", "Hội An", "Huế"]


def test_explicit_itinerary_analysis_is_itinerary_intent():
    e = ConversationIntelligenceEngine()
    r = e.answer("Phân tích hành trình Đà Nẵng - Hội An - Huế giúp tôi")
    assert r["intent"] == "ITINERARY"
    assert "ITINERARY" in r["intents"]


def test_current_status_is_not_generic_destination_answer():
    e = ConversationIntelligenceEngine()
    r = e.answer("Đà Nẵng hôm nay thế nào?")
    assert r["intent"] == "CURRENT_STATUS"
    assert "hôm nay" in r["answer"].lower() or "thời tiết" in r["answer"].lower()


def test_smart_router_prefers_explicit_subject_over_incidental_context():
    e = ConversationIntelligenceEngine()
    assert e.answer("Lịch sử Huế trong mùa mưa cho khách quốc tế")['intent'] == "HISTORY"
    assert e.answer("Cố đô Huế có gì nổi bật? cho khách quốc tế")['intent'] == "DESTINATION"
    assert e.answer("Khách Ấn Độ đến Hội An nên lưu ý gì?")['intent'] == "TOURIST_PROFILE"


def test_multi_place_knowledge_keeps_all_places_in_resolution():
    e = ConversationIntelligenceEngine()
    r = e.answer("Đà Nẵng, Hội An và Huế có gì nổi bật?")
    assert [p['name'] for p in r['places'][:3]] == ["Đà Nẵng", "Hội An", "Huế"]
    assert all(name in r['answer'] for name in ("Đà Nẵng", "Hội An", "Huế"))
