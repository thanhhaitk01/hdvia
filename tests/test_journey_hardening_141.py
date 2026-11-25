from journey_engine import JourneyIntelligenceEngine


def weather(_):
    return [{"date":f"2026-11-{25+i:02d}","condition":"Mưa","code":61 if i<3 else 0,"tmin":24,"tmax":30,"rain":60 if i<3 else 20,"wind":20} for i in range(7)]


def test_alias_resolution_and_order():
    e=JourneyIntelligenceEngine(weather_provider=weather)
    r=e.analyze("Tour", "Ngày 1: sân bay Đà Nẵng → phố cổ Hội An\nNgày 2: thánh địa Mỹ Sơn → Huế")
    assert [p["name"] for p in r["places"]] == ["Đà Nẵng","Hội An","Mỹ Sơn","Huế"]
    assert r["place_resolution"]["aliases"]


def test_ambiguous_place_is_not_silently_guessed():
    e=JourneyIntelligenceEngine(weather_provider=weather)
    r=e.analyze("Tour", "Ngày 1: Chùa Linh Ứng")
    assert len(r["place_resolution"]["ambiguous"]) == 1
    assert r["place_resolution"]["ambiguous"][0]["confidence"] == "LOW"


def test_journey_validation_flags_dense_and_long_day():
    e=JourneyIntelligenceEngine(weather_provider=weather)
    r=e.analyze("Tour", "Ngày 1: Hà Nội → Đà Nẵng → Hội An → Huế → Nha Trang")
    codes={x["code"] for x in r["validation"]}
    assert "DENSE_DAY" in codes
    assert "LONG_TRANSFER" in codes


def test_journey_mutation_adds_place_and_rebuilds_itinerary():
    e=JourneyIntelligenceEngine(weather_provider=weather)
    m=e.mutate_journey("Ngày 1: Đà Nẵng → Hội An\nNgày 2: Huế", "Thêm Mỹ Sơn vào ngày 1")
    assert m["changed"] is True
    assert "Mỹ Sơn" in m["itinerary"]


def test_journey_mutation_moves_place():
    e=JourneyIntelligenceEngine(weather_provider=weather)
    m=e.mutate_journey("Ngày 1: Đà Nẵng → Hội An\nNgày 2: Huế", "Chuyển Hội An sang ngày 2")
    assert m["changed"] is True
    assert "Ngày 2: Huế → Hội An" in m["itinerary"]


def test_explainability_has_evidence():
    e=JourneyIntelligenceEngine(weather_provider=weather)
    r=e.analyze("Tour", "Ngày 1: Hà Nội → Đà Nẵng → Hội An → Huế")
    assert r["explainability"]
    assert all("evidence" in x and "action" in x for x in r["explainability"])
