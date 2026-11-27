from smart_knowledge_acquisition import SmartKnowledgeAcquirer, ALL_DOMAINS

class DeepFakeAdapter:
    def geocode(self, name):
        return {"ok": True, "data": {"results": [{"latitude": 18.35, "longitude": 105.9}]}}
    def wikidata(self, q, limit=5):
        return {"ok": True, "data": {"search": [{"id": "Q1", "label": q, "description": "historical figure or place in Vietnam"}]}}
    def wikipedia(self, q, lang="vi", limit=5):
        return {"ok": True, "data": {"query": {"search": [{"title": q}]}}}
    def wikipedia_page(self, title, lang="vi"):
        return {"ok": True, "data": {"extract": f"{title}: dữ liệu tham khảo {lang}."}}
    def osm_search(self, q, limit=8):
        return {"ok": True, "data": {"results": [{"name": q, "display_name": f"{q}, Vietnam"}]}}

class NoImage:
    def resolve(self, *args, **kwargs): return {"ok": False}

def test_deep_research_covers_people_festival_food_and_landmarks(monkeypatch):
    acq=SmartKnowledgeAcquirer(DeepFakeAdapter())
    monkeypatch.setattr(acq, "image_resolver", NoImage())
    out=acq.acquire("Hà Tĩnh", depth="deep")
    p=out["profile"]
    assert set(p["domains_researched"]) == set(ALL_DOMAINS)
    domains={b["domain"] for b in p["knowledge_blocks"]}
    assert {"people","festival","food","landmarks"}.issubset(domains)
    assert p["research_depth"] == "DEEP"
