from world_acquisition_engine import (
    VERSION, WorldCollector, detect_conflicts, diff_record, discover_sources,
    freshness, media_asset, multilingual_entity, normalize_alias,
)


def test_version_and_sources():
    assert VERSION == "1.30.1-hdv-giau-kinh-nghiem"
    sources = discover_sources("image")
    assert any(x["source_id"] == "wikimedia_commons" for x in sources)
    assert any(x["source_id"] == "openverse" for x in sources)


def test_multilingual_entity_aliases():
    e = multilingual_entity("Chùa Cầu Hội An", ["Japanese Covered Bridge", "Lai Vien Kieu"])
    assert "Japanese Covered Bridge" in e["aliases"]
    assert normalize_alias("Chùa Cầu Hội An") == "chùa cầu hội an"
    assert e["status"] == "CANDIDATE"


def test_media_provenance_and_freshness():
    m = media_asset(entity_id="ent:1", url="https://example.org/a.jpg", source_id="openverse", license="CC BY", attribution="Creator")
    assert m["source_id"] == "openverse"
    assert m["retrieved_at"]
    assert m["freshness"] == "FRESH"
    assert m["status"] == "CANDIDATE"


def test_incremental_update_states():
    row = {"name": "A", "value": 1}
    assert diff_record(None, row)["state"] == "NEW"
    assert diff_record(row, row)["state"] == "UNCHANGED"
    assert diff_record(row, {"name": "A", "value": 2})["state"] == "CHANGED"


def test_conflict_detection():
    conflicts = detect_conflicts([
        {"subject": "Chùa Cầu", "predicate": "built_year", "object": 1593, "source": "A"},
        {"subject": "Chùa Cầu", "predicate": "built_year", "object": 1600, "source": "B"},
    ])
    assert len(conflicts) == 1
    assert conflicts[0]["resolution"] == "REVIEW_REQUIRED"


def test_world_collector_is_review_safe():
    out = WorldCollector().package(target="Đà Nẵng", knowledge=[{"title": "test", "content": "x"}], media=[{"url": "https://example.org/x.jpg"}], claims=[])
    assert out["publication_policy"] == "CANDIDATE_ONLY"
    assert out["ready_for_governance"] is True
    assert out["knowledge"][0]["status"] == "CANDIDATE"
    assert out["media"][0]["status"] == "CANDIDATE"
