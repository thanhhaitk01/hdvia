from journey_engine.engine import JourneyIntelligenceEngine
from knowledge_intelligence import destination_card
from knowledge_graph import build
from knowledge_quality import assess


def test_knowledge_graph_marks_external_nodes_unverified():
    g=build("Đà Nẵng", live={"wikipedia":{"results":[{"title":"Da Nang"}]}})
    assert g["version"] == "1.1.0"
    assert any(n.get("verified") is False for n in g["nodes"]["place"])


def test_destination_card_has_quality_and_graph():
    c=destination_card("Hội An")
    assert "knowledge_graph" in c
    assert "knowledge_quality" in c
    assert c["knowledge_quality"]["verified_rule"]


def test_quality_is_bounded_and_explainable():
    q=assess({"source":"OpenStreetMap","source_type":"external"}, ["OpenStreetMap"])
    assert 0 <= q["score"] <= 1
    assert q["corroboration_count"] == 1


def test_journey_feasibility_and_decision_trace():
    e=JourneyIntelligenceEngine(weather_provider=lambda p: [{"date":"2099-01-01","condition":"clear","code":0,"tmin":20,"tmax":25,"rain":0,"wind":10}]*7)
    r=e.analyze("Test", "Ngày 1: Đà Nẵng → Hội An")
    assert r["version"] == "1.22.0"
    assert "feasibility" in r and r["feasibility"]["traffic"]
    assert "decision_trace" in r
    assert all("source" in x for x in r["decision_trace"])


def test_tour_intelligence_preserves_requested_4d3n_structure():
    e=JourneyIntelligenceEngine(weather_provider=lambda p: [{"date":"2099-01-01","condition":"clear","code":0,"tmin":20,"tmax":25,"rain":0,"wind":10}]*7)
    r=e.analyze("Phú Quốc 4 ngày 3 đêm", "PHÚ QUỐC 4 NGÀY 3 ĐÊM CHO 10 KHÁCH ẤN ĐỘ")
    ti=r["tour_intelligence"]
    assert ti["requested_days"] == 4
    assert len(ti["candidates"]) == 4
    assert all(len(c["daily_plan"]) == 4 for c in ti["candidates"])
    assert all("role" in d and "title" in d and "anchors" in d for d in ti["candidates"][0]["daily_plan"])
    assert all("integrity_note" in c for c in ti["candidates"])
