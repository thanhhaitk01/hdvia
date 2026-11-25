from conversation_engine import ConversationIntelligenceEngine


def test_vietnam_wide_place_resolution():
    e=ConversationIntelligenceEngine()
    for q, expected in [("Ninh Bình", "Ninh Bình"), ("Cao Bằng", "Cao Bằng"), ("Phú Quốc", "Phú Quốc"), ("Cà Mau", "Cà Mau")]:
        places=e.resolve_places(q)
        assert places and expected in places[0]["name"]


def test_multi_intent_understanding():
    e=ConversationIntelligenceEngine()
    intents=e.detect_intents("Khách Ấn Độ đi Huế, nếu mưa thì nên thuyết minh và đổi lịch thế nào?")
    assert "WEATHER" in intents
    assert "TOURIST_PROFILE" in intents
    assert "GUIDE_SCRIPT" in intents or "PLAN_B" in intents


def test_predicts_followup_questions():
    e=ConversationIntelligenceEngine()
    q=e.predict_questions("Lăng Khải Định")
    assert len(q)>=3
    assert any("thuyết minh" in x.lower() for x in q)


def test_unknown_does_not_invent_facts():
    e=ConversationIntelligenceEngine()
    r=e.answer("Một địa điểm không có trong kho dữ liệu HDVIA")
    assert r["confidence"] == "LOW"
    assert "chưa có nguồn dữ liệu đủ tin cậy" in r["answer"]
def test_high_frequency_landmark_aliases_resolve():
    e = ConversationIntelligenceEngine()
    assert [x["name"] for x in e.resolve_places("Bà Nà lịch sử")] == ["Bà Nà Hills"]
    assert [x["name"] for x in e.resolve_places("Ba Na văn hóa")] == ["Bà Nà Hills"]
    assert [x["name"] for x in e.resolve_places("Linh Ứng văn hóa")] == ["Chùa Linh Ứng Sơn Trà"]
