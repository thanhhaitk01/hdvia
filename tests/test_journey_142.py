from journey_engine import JourneyIntelligenceEngine

def weather(_):
    return [{"date":f"2026-11-{25+i:02d}","condition":"Trời quang","code":0,"tmin":20,"tmax":28,"rain":10,"wind":10} for i in range(7)]

def test_ambiguous_blocks_silent_route_resolution():
    e=JourneyIntelligenceEngine(weather_provider=weather, geocoder=lambda _: None)
    r=e.analyze("Tour", "Ngày 1: Chùa Linh Ứng → Hội An")
    assert r["pending_clarification"]
    assert r["pending_clarification"][0]["type"] == "AMBIGUOUS_DESTINATION"
    assert "Chùa Linh Ứng" not in r["days"][0]["places"]
    assert any(x["code"] == "AMBIGUOUS_DESTINATION" for x in r["validation"])

def test_natural_mutation_variants():
    e=JourneyIntelligenceEngine(weather_provider=weather)
    base="Ngày 1: Đà Nẵng → Hội An\nNgày 2: Huế\nNgày 3: Mỹ Sơn"
    cases=[
        ("Đổi ngày 2 sang Hội An", "Ngày 2: Hội An"),
        ("Ngày 2 đổi thành Hội An", "Ngày 2: Hội An"),
        ("Cho Hội An xuống ngày 3", "Ngày 3: Mỹ Sơn → Hội An"),
        ("Đổi Hội An sang ngày 2", "Ngày 2: Huế → Hội An"),
        ("Ngày 1 thêm Sơn Trà", "Ngày 1: Đà Nẵng → Hội An → Sơn Trà"),
    ]
    for cmd, expected in cases:
        m=e.mutate_journey(base,cmd)
        assert m["changed"] is True, cmd
        assert expected in m["itinerary"], (cmd,m["itinerary"])

def test_time_feasibility_and_calendar_weather():
    e=JourneyIntelligenceEngine(weather_provider=weather)
    r=e.analyze("Tour", "Ngày 1: 08:00-10:00 Đà Nẵng → Hội An, tham quan, ăn trưa", start_date="2026-11-25")
    assert r["start_date"] == "2026-11-25"
    assert r["calendar_weather"]["Đà Nẵng"][1] is not None
    assert any(x["code"] in ("TIME_INFEASIBLE","TIME_TIGHT") for x in r["validation"])
