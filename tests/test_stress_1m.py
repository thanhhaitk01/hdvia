import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from journey_engine import JourneyIntelligenceEngine
from journey_engine.engine import haversine_km

def test_one_million_core_logic_iterations():
    e=JourneyIntelligenceEngine(weather_provider=lambda p:[{"date":"2026-11-21","condition":"Trời quang","code":0,"tmin":20,"tmax":28,"rain":10,"wind":10}]*7)
    for i in range(1_000_000):
        mode=i%5
        if mode==0:
            assert e.detect_places('Ngày 1: Đà Nẵng → Hội An')[0]['name']=='Đà Nẵng'
        elif mode==1:
            assert len(e.parse_days('Ngày 1: Huế\nNgày 2: Đà Nẵng'))==2
        elif mode==2:
            w=e._normalize_weather([]); assert len(w)==7
        elif mode==3:
            assert e.risk([{"code":0,"rain":10,"wind":10,"tmax":28}]*7)['level']=='LOW'
        else:
            assert haversine_km({'lat':16.0544,'lon':108.2022},{'lat':15.8801,'lon':108.3380})>0

def test_one_thousand_full_deterministic_analyses():
    e=JourneyIntelligenceEngine(weather_provider=lambda p:[{"date":"2026-11-21","condition":"Trời quang","code":0,"tmin":20,"tmax":28,"rain":10,"wind":10}]*7)
    for _ in range(1000):
        r=e.analyze('HDVIA 1.8','Ngày 1: Đà Nẵng → Hội An\nNgày 2: Hội An → Huế')
        assert r['version']=='1.22.0'
        assert len(r['weather']['Đà Nẵng'])==7
        assert len(r['weather']['Hội An'])==7
        assert len(r['weather']['Huế'])==7
        assert r['quality']['score']>=0
