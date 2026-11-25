import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from journey_engine import JourneyIntelligenceEngine

def test_parse_known_places():
    e=JourneyIntelligenceEngine(weather_provider=lambda p: [])
    r=e.analyze('demo','Ngày 1: Huế\nNgày 2: Đà Nẵng → Hội An')
    assert 'Huế' in [p['name'] for p in r['places']
]
    assert 'Đà Nẵng' in [p['name'] for p in r['places']]
    assert 'Hội An' in [p['name'] for p in r['places']]

def test_analyze_returns_weather_for_every_detected_place():
    weather=lambda p:[{"date":"2026-11-21","condition":"Trời quang","code":0,"tmin":20,"tmax":28,"rain":10,"wind":10}]*7
    e=JourneyIntelligenceEngine(weather_provider=weather)
    r=e.analyze('demo','Ngày 1: Huế\nNgày 2: Đà Nẵng → Hội An')
    assert set(r['weather'])=={'Huế','Đà Nẵng','Hội An'}
    assert all(len(r['weather'][name])==7 for name in r['weather'])
    assert all(len(day['places']) for day in r['days'])

def test_engine_version_matches_v1_8():
    e=JourneyIntelligenceEngine(weather_provider=lambda p: [])
    assert e.VERSION=='1.14.5'

def test_v18_builds_briefing_plan_b_and_quality():
    e=JourneyIntelligenceEngine(weather_provider=lambda p:[{"date":"2026-11-21","condition":"Trời quang","code":0,"tmin":20,"tmax":28,"rain":10,"wind":10}]*7)
    r=e.analyze('demo','Ngày 1: Huế\nNgày 2: Đà Nẵng → Hội An')
    assert len(r['briefing'])==2
    assert len(r['plan_b'])==2
    assert r['confidence']=='HIGH'
    assert r['quality']['score']==100

def test_weather_contract_is_exactly_seven_days_even_if_provider_is_partial():
    e=JourneyIntelligenceEngine(weather_provider=lambda p:[{"date":"2026-11-21","condition":"Trời quang","code":0,"tmin":20,"tmax":28,"rain":10,"wind":10}])
    r=e.analyze('demo','Ngày 1: Huế')
    assert len(r['weather']['Huế'])==7
    assert r['weather']['Huế'][1]['code']==-1
