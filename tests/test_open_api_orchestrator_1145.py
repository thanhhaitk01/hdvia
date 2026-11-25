from api_adapters import OpenAPIAdapter, API_LAYER_VERSION


def test_orchestrator_status_and_providers():
    s = OpenAPIAdapter().status()
    assert s["version"] == API_LAYER_VERSION
    assert {"weather","geocoding","routing","air_quality","marine","osm","wikidata","wikipedia","sun","opentripmap"} <= set(s["providers"])


def test_optional_key_provider_fails_closed(monkeypatch):
    monkeypatch.delenv("OPENTRIPMAP_API_KEY", raising=False)
    a = OpenAPIAdapter(); a.live_opentripmap = True
    out = a.opentripmap_places(16.05,108.2)
    assert out["ok"] is False and out["disabled"] is True


def test_enrich_destination_contract(monkeypatch):
    a=OpenAPIAdapter()
    monkeypatch.setattr(a, "geocode", lambda name: {"ok": True, "data":{"results":[{"latitude":16.05,"longitude":108.2}]}})
    monkeypatch.setattr(a, "weather", lambda *args: {"ok":True,"provider":"open_meteo"})
    monkeypatch.setattr(a, "air_quality", lambda *args: {"ok":True,"provider":"open_meteo_air_quality"})
    monkeypatch.setattr(a, "sun", lambda *args: {"ok":True,"provider":"sunrise_sunset"})
    monkeypatch.setattr(a, "marine", lambda *args: {"ok":True,"provider":"open_meteo_marine"})
    monkeypatch.setattr(a, "osm_search", lambda *args: {"ok":True,"provider":"osm_nominatim"})
    monkeypatch.setattr(a, "opentripmap_places", lambda *args: {"ok":False,"disabled":True,"provider":"opentripmap"})
    monkeypatch.setattr(a, "wikidata", lambda *args: {"ok":True,"provider":"wikidata"})
    monkeypatch.setattr(a, "wikipedia", lambda *args: {"ok":True,"provider":"wikipedia"})
    out=a.enrich_destination("Đà Nẵng")
    assert out["ok"] is True
    assert out["coordinates"] == {"lat":16.05,"lon":108.2}
    assert out["wikidata"]["ok"] is True
    assert out["weather"]["provider"] == "open_meteo"
