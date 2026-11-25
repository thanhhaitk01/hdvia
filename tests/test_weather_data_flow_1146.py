import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from journey_engine.engine import JourneyIntelligenceEngine


def _weather(_place):
    return [
        {"date":"2026-11-25","condition":"Mưa nhẹ","code":61,"tmin":20,"tmax":27,"rain":10,"wind":10},
        {"date":"2026-11-26","condition":"Mưa to","code":65,"tmin":20,"tmax":26,"rain":90,"wind":20},
        {"date":"2026-11-27","condition":"Trời quang","code":0,"tmin":21,"tmax":28,"rain":5,"wind":12},
        {"date":"2026-11-28","condition":"Trời quang","code":0,"tmin":21,"tmax":29,"rain":5,"wind":12},
        {"date":"2026-11-29","condition":"Trời quang","code":0,"tmin":21,"tmax":29,"rain":5,"wind":12},
        {"date":"2026-11-30","condition":"Trời quang","code":0,"tmin":21,"tmax":29,"rain":5,"wind":12},
        {"date":"2026-12-01","condition":"Trời quang","code":0,"tmin":21,"tmax":29,"rain":5,"wind":12},
    ]


def test_weather_impact_uses_forecast_slot_per_day_without_start_date():
    e=JourneyIntelligenceEngine(weather_provider=_weather)
    r=e.analyze("Tour", "Ngày 1: Đà Nẵng\nNgày 2: Hội An")
    assert r["weather_impact"][0]["max_rain_probability"] == 10
    assert r["weather_impact"][0]["level"] == "LOW"
    assert r["weather_impact"][1]["max_rain_probability"] == 90
    assert r["weather_impact"][1]["level"] == "HIGH"
    assert r["weather_impact"][1]["forecast_basis"] == "forecast_slot"


def test_weather_impact_uses_calendar_date_when_start_date_is_supplied():
    e=JourneyIntelligenceEngine(weather_provider=_weather)
    r=e.analyze("Tour", "Ngày 1: Đà Nẵng\nNgày 2: Hội An", start_date="2026-11-25")
    assert r["start_date"] == "2026-11-25"
    assert r["calendar_weather"]["Đà Nẵng"][1]["date"] == "2026-11-25"
    assert r["calendar_weather"]["Đà Nẵng"][2]["date"] == "2026-11-26"
    assert r["weather_impact"][0]["max_rain_probability"] == 10
    assert r["weather_impact"][1]["max_rain_probability"] == 90
    assert r["weather_impact"][1]["forecast_basis"] == "calendar_date"


def test_weather_normalization_preserves_provider_date_order():
    e=JourneyIntelligenceEngine(weather_provider=lambda p: _weather(p)[:2])
    r=e.analyze("Tour", "Ngày 1: Đà Nẵng")
    dates=[x["date"] for x in r["weather"]["Đà Nẵng"]]
    assert dates[:2] == ["2026-11-25","2026-11-26"]
    assert len(dates) == 7
