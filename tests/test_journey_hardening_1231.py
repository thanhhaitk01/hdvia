from conversation_engine import ConversationIntelligenceEngine
from journey_engine.engine import JourneyIntelligenceEngine


def test_compact_multi_place_duration_is_itinerary():
    engine = ConversationIntelligenceEngine()
    q = "Đà Nẵng - Hội An - Huế 3 ngày"
    assert "ITINERARY" in engine.detect_intents(q)
    assert engine._primary_intent(q, engine.detect_intents(q)) == "ITINERARY"


def test_compact_multi_place_duration_preserves_all_days():
    result = JourneyIntelligenceEngine().analyze("Hành trình miền Trung", "Đà Nẵng - Hội An - Huế 3 ngày")
    assert [(d["day"], d["places"]) for d in result["days"]] == [
        (1, ["Đà Nẵng"]), (2, ["Hội An"]), (3, ["Huế"])
    ]


def test_unknown_weather_metrics_are_not_marked_low():
    result = JourneyIntelligenceEngine().analyze("Hành trình", "Đà Nẵng 2 ngày")
    assert all(item["level"] == "UNKNOWN" for item in result["weather_impact"])


