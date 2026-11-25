from api_adapters import OpenAPIAdapter, API_LAYER_VERSION

def test_adapter_status_contract():
    s=OpenAPIAdapter().status()
    assert s["version"] == API_LAYER_VERSION
    assert {"weather","geocoding","routing"} <= set(s["providers"])

def test_weather_adapter_normalizes_public_response(monkeypatch):
    a=OpenAPIAdapter()
    monkeypatch.setattr("api_adapters.open_meteo_weather", lambda *args: {"ok":True,"provider":"open_meteo","data":{"daily":{"time":["2026-11-25"],"weather_code":[61],"temperature_2m_min":[20],"temperature_2m_max":[27],"precipitation_probability_max":[80],"wind_speed_10m_max":[25]}}})
    out=a.weather(16.05,108.2,7)
    assert out["ok"] is True and out["provider"] == "open_meteo"

def test_routing_is_safe_off_by_default():
    a=OpenAPIAdapter()
    a.live_routing=False
    out=a.route("108.2,16.05;108.3,15.88")
    assert out["ok"] is False and out["disabled"] is True

def test_journey_engine_uses_live_route_when_enabled(monkeypatch):
    from journey_engine.engine import JourneyIntelligenceEngine
    monkeypatch.setattr("journey_engine.engine.OPEN_API_ADAPTER.route", lambda coords: {
        "ok": True, "data": {"routes": [{"distance": 123400.0, "duration": 11100.0}]}, "provider": "osrm"
    })
    monkeypatch.setattr("journey_engine.engine.OPEN_API_ADAPTER.geocode", lambda name: {"ok":False})
    monkeypatch.setattr("journey_engine.engine.OPEN_API_ADAPTER.weather", lambda *args: {"ok":False})
    monkeypatch.setattr("journey_engine.engine.OPEN_API_ADAPTER.live_routing", True)
    e=JourneyIntelligenceEngine(weather_provider=lambda p: [], geocoder=lambda n: None)
    r=e.analyze("Tour", "Ngày 1: Đà Nẵng → Hội An")
    assert r["days"][0]["routing_source"] == "osrm-live"
    assert r["days"][0]["estimated_drive_minutes"] == 185
