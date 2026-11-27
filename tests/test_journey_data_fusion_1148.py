from journey_data_fusion import JourneyDataFusion


class FakeAdapter:
    def geocode(self, name):
        return {"ok": True, "provider": "fake-geocode", "data": {"results": [{"name": name, "latitude": 16.0, "longitude": 108.0}]}}

    def air_quality(self, lat, lon):
        return {"ok": True, "provider": "fake-aqi", "data": {"hourly": {"time": ["2026-11-25T12:00"], "european_aqi": [42]}}}

    def sun(self, lat, lon):
        return {"ok": True, "provider": "fake-sun", "data": {"sunrise": "2026-11-25T05:50:00+07:00", "sunset": "2026-11-25T17:15:00+07:00"}}

    def marine(self, lat, lon):
        return {"ok": True, "provider": "fake-marine", "data": {"hourly": {"time": ["2026-11-25T12:00"], "wave_height": [0.7], "wave_period": [7.2]}}}

    def osm_search(self, q, limit=5):
        return {"ok": True, "provider": "fake-osm", "data": {"results": [{"display_name": q + ", Vietnam", "lat": "16", "lon": "108"}]}}

    def wikipedia(self, q, lang="vi", limit=5):
        return {"ok": True, "provider": "fake-wiki", "data": {"results": [{"title": q, "snippet": "Thông tin kiểm thử"}]}}

    def wikidata(self, q, limit=5):
        return {"ok": True, "provider": "fake-wikidata", "data": {"results": [{"label": q, "description": "Mục kiểm thử"}]}}


def test_fusion_builds_one_unified_live_package():
    f = JourneyDataFusion(adapter=FakeAdapter())
    result = f.enrich_result({
        "places": [{"name": "Đà Nẵng", "lat": 16.0544, "lon": 108.2022}],
        "weather": {"Đà Nẵng": [{"date": "2026-11-25", "tmax": 28}]},
    })
    live = result["live_data_fusion"]
    assert live["enabled"] is True
    d = live["destinations"]["Đà Nẵng"]
    assert d["coordinates"]["lat"] == 16.0544
    assert d["air_quality"]["summary"]["value"] == 42
    assert d["sun"]["summary"]["sunrise"]
    assert d["marine"]["summary"]["wave_height"] == 0.7
    assert d["wikipedia"]["results"][0]["title"] == "Đà Nẵng"
    assert "OpenStreetMap" in d["sources"]


def test_fusion_isolates_provider_failure():
    class Broken(FakeAdapter):
        def wikipedia(self, q, lang="vi", limit=5):
            raise RuntimeError("provider down")

    f = JourneyDataFusion(adapter=Broken())
    result = f.enrich_result({"places": [{"name": "Huế", "lat": 16.46, "lon": 107.59}], "weather": {}})
    d = result["live_data_fusion"]["destinations"]["Huế"]
    assert d["providers"]["wikipedia"]["ok"] is False
    assert d["availability"] in ("LIVE_PARTIAL", "CURATED_ONLY")
    assert d["air_quality"]["summary"]["value"] == 42


def test_fusion_respects_place_budget(monkeypatch):
    monkeypatch.setenv("HDVIA_JOURNEY_FUSION_MAX_PLACES", "2")
    f = JourneyDataFusion(adapter=FakeAdapter())
    result = f.enrich_result({"places": [{"name": str(i), "lat": 16, "lon": 108} for i in range(5)], "weather": {}})
    assert len(result["live_data_fusion"]["destinations"]) == 2


def test_entity_resolution_bridges_vietnamese_landmark_to_wikidata():
    class AliasAdapter(FakeAdapter):
        def wikipedia(self, q, lang="vi", limit=5):
            if lang == "en":
                return {"ok": True, "provider": "fake-wiki-en", "data": {"results": [{"title": "Japanese Bridge", "snippet": "Japanese Bridge in Hoi An, Vietnam"}]}}
            return {"ok": True, "provider": "fake-wiki", "data": {"results": [{"title": "Chùa Cầu", "snippet": "Di tích ở Hội An"}]}}

        def wikidata(self, q, limit=5):
            if q in ("Japanese Bridge", "Hoi An Japanese Bridge"):
                return {"ok": True, "provider": "fake-wikidata", "data": {"search": [{"id": "Q1091054", "label": "Japanese Bridge", "description": "bridge in Hoi An, Vietnam"}]}}
            return {"ok": True, "provider": "fake-wikidata", "data": {"search": []}}

    f = JourneyDataFusion(adapter=AliasAdapter())
    result = f.enrich_result({"places": [{"name": "Chùa Cầu Hội An", "lat": 15.8771541, "lon": 108.3260034}], "weather": {}})
    d = result["live_data_fusion"]["destinations"]["Chùa Cầu Hội An"]
    assert d["entity_resolution"]["wikidata"]["id"] == "Q1091054"
    assert d["entity_resolution"]["wikidata"]["label"] == "Japanese Bridge"
    assert d["entity_resolution"]["confidence"] in ("HIGH", "MEDIUM")
    assert d["wikidata"]["resolved"]["id"] == "Q1091054"
