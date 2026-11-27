from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from place_intelligence import guide_actions, build_place_intelligence


def test_rain_and_water_warning_becomes_guide_action():
    forecast=[{"date":"2026-11-27","rain":80,"wind":42,"tmax":31,"code":81}]
    actions=guide_actions("Hồ Phú Ninh",forecast,{},"đi hồ Phú Ninh")
    joined=" ".join(actions).lower()
    assert "áo mưa" in joined
    assert "thuyền" in joined or "cano" in joined


def test_heat_warning_becomes_packing_action():
    forecast=[{"date":"2026-11-27","rain":10,"wind":12,"tmax":36,"code":1}]
    actions=guide_actions("Điểm tham quan",forecast,{},"tham quan")
    assert any("nước uống" in x.lower() for x in actions)


def test_place_intelligence_keeps_point_weather_anchor_and_admin_fields():
    point={"name":"Hồ Phú Ninh","lat":15.75,"lon":108.10}
    pi=build_place_intelligence(point,[{"date":"2026-11-27","rain":10,"wind":10,"tmax":28,"code":1}],"Hồ Phú Ninh")
    assert pi["weather_anchor"]["level"] == "POINT"
    assert pi["weather_anchor"]["refresh_policy"] == "on_query + scheduled_watch"
    assert "local_admin" in pi


def test_severe_weather_is_not_reported_as_safe():
    forecast=[{"date":"2026-11-27","rain":20,"wind":50,"tmax":29,"code":95}]
    actions=guide_actions("Hồ Phú Ninh",forecast,{},"đi thuyền")
    joined=" ".join(actions).lower()
    assert "dông mạnh" in joined
    assert "an toàn" in joined
