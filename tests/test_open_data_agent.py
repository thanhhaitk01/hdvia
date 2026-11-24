import json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import open_data_agent as agent


def test_source_policy_allows_only_registered_open_sources():
    assert agent.allowed_for_auto("wikimedia_vi")
    assert agent.allowed_for_auto("nominatim_osm")
    assert not any(agent.allowed_for_auto(x) for x in ("vietravel", "saigontourist") if x in agent.SOURCES)


def test_wikimedia_candidate_is_candidate_only():
    rec = agent.make_wikimedia_candidate("Huế", {"url": "https://vi.wikipedia.org/wiki/Hu%E1%BA%BF", "title": "Huế", "text": "Nội dung kiểm chứng của Wikipedia đủ dài để tạo candidate trong bài kiểm thử." * 3})
    assert rec["status"] == "CANDIDATE"
    assert rec["source_id"] == "wikimedia_vi"
    assert rec["license"]
    assert rec["attribution"]


def test_osm_candidate_has_coordinates_and_attribution():
    rec = agent.make_osm_candidate("Huế", {"lat": "16.46", "lon": "107.59", "display_name": "Huế, Việt Nam", "type": "city", "class": "place", "address": {}})
    assert rec["status"] == "CANDIDATE"
    payload = json.loads(rec["content"])
    assert payload["lat"] == "16.46"
    assert rec["license"] == "ODbL"


def test_agent_is_bounded_and_deterministic(monkeypatch, tmp_path):
    monkeypatch.setattr(agent, "INBOX", tmp_path / "candidates.json")
    monkeypatch.setattr(agent, "STATE", tmp_path / "state.json")
    monkeypatch.setattr(agent, "wikimedia_search_extract", lambda q: [{"title": q, "text": "Nội dung đủ dài." * 20, "url": f"https://vi.wikipedia.org/wiki/{q}"}])
    monkeypatch.setattr(agent, "nominatim_search", lambda q: [{"lat": "16", "lon": "107", "display_name": q, "type": "city", "class": "place", "address": {}}])
    monkeypatch.setattr(agent.time, "sleep", lambda *_: None)
    monkeypatch.setattr(agent, "DEFAULT_TARGETS", ["Huế"])
    first = agent.run(["Huế"])
    second = agent.run(["Huế"])
    assert first["new"] == 2
    assert second["new"] == 0
    assert second["duplicates"] == 2
