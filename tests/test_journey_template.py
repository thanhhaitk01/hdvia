from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_journey_template_renders_weather_for_each_result_place():
    html = (ROOT / "templates" / "journey.html").read_text(encoding="utf-8")
    assert "result.places" in html
    assert "result.weather.get(p.name, [])" in html
    assert "Thời tiết 7 ngày theo điểm" in html
