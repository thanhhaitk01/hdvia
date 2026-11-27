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


def test_action_intent_priority_for_rain_plan_b():
    e=ConversationIntelligenceEngine()
    r=e.answer("Nếu trời mưa ở Huế thì Plan B là gì?")
    assert r["intent"] == "PLAN_B"
    assert "WEATHER" in r["intents"]


def test_route_phrase_must_cover_mat_bao_lau():
    e=ConversationIntelligenceEngine()
    r=e.answer("Từ Đà Nẵng đi Hội An mất bao lâu?")
    assert r["intent"] == "ROUTE"
    assert "ROUTE" in r["intents"]


def test_explicit_subject_beats_incidental_weather_context():
    e=ConversationIntelligenceEngine()
    assert e.answer("Lịch sử Tháp Bà Ponagar có gì đáng kể? trong mùa mưa")["intent"] == "HISTORY"


def test_explicit_subject_beats_incidental_tourist_context():
    e=ConversationIntelligenceEngine()
    assert e.answer("Cố đô Huế có gì nổi bật? cho khách quốc tế")["intent"] == "DESTINATION"


def test_source_question_gets_knowledge_gap_priority():
    e=ConversationIntelligenceEngine()
    assert e.answer("Nguồn chính thức về Phong Nha – Kẻ Bàng là gì?")["intent"] == "KNOWLEDGE_GAP"


def test_route_without_journey_is_explicit_estimate_not_live():
    e=ConversationIntelligenceEngine()
    r=e.answer("Từ Đà Nẵng đi Hội An mất bao lâu?")
    assert r["intent"] == "ROUTE"
    assert r["data_status"] == "ESTIMATE"
    assert "không phải" in r["answer"].lower()


def test_plan_b_without_live_context_does_not_invent_alternative():
    e=ConversationIntelligenceEngine()
    r=e.answer("Nếu trời mưa ở Huế thì Plan B là gì?")
    assert r["intent"] == "PLAN_B"
    assert r["data_status"] == "UNKNOWN"
    assert "Không tự bịa" in r["answer"]


def test_tourist_profile_does_not_stereotype_without_verified_profile():
    e=ConversationIntelligenceEngine()
    r=e.answer("Khách Ấn Độ đến Hội An nên lưu ý gì?")
    assert r["intent"] == "TOURIST_PROFILE"
    assert r["data_status"] == "UNKNOWN"
    assert "không suy diễn" in r["answer"]
