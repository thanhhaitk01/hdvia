from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from journey_engine import JourneyIntelligenceEngine


def weather(_p):
    return [{"date":f"2026-11-{25+i:02d}","condition":"Mưa","code":61,"tmin":23,"tmax":29,"rain":55,"wind":20} for i in range(7)]

def test_natural_day_markers_are_split():
    e=JourneyIntelligenceEngine(weather_provider=weather)
    days=e.parse_days("Ngày 1 Đà Nẵng, Ngày 2 Hội An, Ngày 3 Huế")
    assert [d["day"] for d in days]==[1,2,3]
    assert [d["places"][0]["name"] for d in days]==["Đà Nẵng","Hội An","Huế"]

def test_journey_has_time_weather_impact_and_memory():
    e=JourneyIntelligenceEngine(weather_provider=weather)
    r=e.analyze("Tour miền Trung", "Ngày 1: Đà Nẵng → Hội An\nNgày 2: Hội An → Huế")
    assert r["version"]=="1.15.0"
    assert all("estimated_drive_minutes" in d for d in r["days"])
    assert len(r["weather_impact"])==2
    assert r["journey_memory"]["places"]==["Đà Nẵng","Hội An","Huế"]
    assert all("plan_c" in p for p in r["plan_b"])
