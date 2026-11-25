from journey_engine import JourneyIntelligenceEngine


def test_known_vietnam_tourism_hub_is_not_silently_dropped():
    e=JourneyIntelligenceEngine(weather_provider=lambda p: [])
    r=e.analyze('VN coverage', 'Ngày 1: Bản Giốc → Hà Nội')
    names=r['days'][0]['places']
    assert 'Bản Giốc' in names and 'Hà Nội' in names
    assert any(x['code']=='PLACE_COORDINATES_REQUIRED' for x in r['validation'])
    assert r['days'][0]['distance_km'] is None


def test_catalogued_landmark_is_recognized_without_false_route_precision():
    e=JourneyIntelligenceEngine(weather_provider=lambda p: [])
    r=e.analyze('VN coverage', 'Ngày 1: Bản Giốc')
    assert r['days'][0]['places'] == ['Bản Giốc']
    assert r['days'][0]['distance_km'] == 0
