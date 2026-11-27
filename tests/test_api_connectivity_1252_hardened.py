from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_connectivity_route_has_canonical_and_trailing_slash_alias():
    src = (ROOT / "app.py").read_text(encoding="utf8")
    assert '@app.get("/api/v1/public-api/connectivity")' in src
    assert '@app.get("/api/v1/public-api/connectivity/")' in src


def test_connectivity_probe_reports_live_error_and_summary():
    src = (ROOT / "api_adapters.py").read_text(encoding="utf8")
    assert '"status": "LIVE"' in src
    assert '"status": "ERROR"' in src
    assert '"summary": {"live": live, "error": total - live, "total": total}' in src
    assert 'bypasses HDVIA feature' in src


def test_connectivity_probe_covers_nine_provider_groups():
    src = (ROOT / "api_adapters.py").read_text(encoding="utf8")
    for name in ["weather", "geocoding", "routing", "air_quality", "marine", "osm", "wikipedia", "wikidata", "sun"]:
        assert f'"{name}": lambda' in src
