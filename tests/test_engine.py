from journey_engine import JourneyIntelligenceEngine

def test_parse_known_places():
    e=JourneyIntelligenceEngine(weather_provider=lambda p: [])
    r=e.analyze('demo','Ngày 1: Huế\nNgày 2: Đà Nẵng → Hội An')
    assert 'Huế' in [p['name'] for p in r['places']]
    assert 'Đà Nẵng' in [p['name'] for p in r['places']]
    assert 'Hội An' in [p['name'] for p in r['places']]
