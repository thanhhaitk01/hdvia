from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[1]

def test_app_compiles_and_keeps_existing_routes():
    src=(ROOT/"app.py").read_text(encoding="utf8")
    ast.parse(src)
    for route in ["/","/journey","/api/v1/journey/analyze","/api/v1/weather","/api/v1/place-image","/api/v1/route","/health","/profile","/guide/apply","/admin/guides","/admin/audit"]:
        assert route in src

def test_v16_feedback_route_exists():
    src=(ROOT/"app.py").read_text(encoding="utf8")
    assert "/api/v1/journey/feedback" in src
    assert "journey_feedback" in src
