from conversation_engine import ConversationIntelligenceEngine


def test_weather_question_never_falls_back_to_destination_catalog():
    e = ConversationIntelligenceEngine()
    r = e.answer("Đà Nẵng mùa này có mưa không?")
    assert r["intent"] == "WEATHER"
    assert r["data_status"] == "UNKNOWN"
    assert "thời tiết" in r["answer"].lower()
    assert "đô thị biển" not in r["answer"].lower()


def test_weather_with_degraded_forecast_stays_in_weather_module():
    e = ConversationIntelligenceEngine()
    journey = {
        "weather": {
            "Đà Nẵng": [{"date": "2026-11-27", "condition": "Chưa có dữ liệu", "rain": None, "tmin": None, "tmax": None} for _ in range(7)]
        }
    }
    r = e.answer("Đà Nẵng mùa này có mưa không?", journey=journey)
    assert r["intent"] == "WEATHER"
    assert r["data_status"] == "UNKNOWN"
    assert "đô thị biển" not in r["answer"].lower()
