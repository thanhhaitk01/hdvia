from pathlib import Path
import json

BASE = Path(__file__).resolve().parents[1]


def test_representative_image_metadata_is_exposed_in_journey_context_source():
    app = (BASE / "app.py").read_text(encoding="utf-8")
    assert '"image_query":d["name"] + " Vietnam"' in app
    assert 'load_reference_warehouse()' in app


def test_journey_template_has_lightweight_representative_image_hook():
    html = (BASE / "templates" / "journey.html").read_text(encoding="utf-8")
    assert 'data-place-image' in html
    assert '/api/v1/place-image?name=' in html
    assert 'Ảnh: Wikimedia Commons' in html


def test_kpd_reference_records_remain_compact_and_attributed():
    data = json.loads((BASE / "data/warehouse/khamphadisan_seed_2026.json").read_text(encoding="utf-8"))
    assert data["policy"] == "compact_structured_reference_only"
    assert all(r.get("source") for r in data["records"])
    assert all(r.get("status") in {"REFERENCE", "DISCOVERY_SOURCE", "SOURCE_INDEX"} for r in data["records"])
