from smart_knowledge_acquisition import SmartKnowledgeAcquirer


class FakeAdapter:
    def geocode(self, name):
        return {"ok": True, "data": {"results": [{"latitude": 16.0544, "longitude": 108.2022}]}}
    def wikidata(self, q, limit=5):
        return {"ok": True, "data": {"search": [{"id": "Q5119", "label": "Da Nang", "description": "city in Vietnam"}]}}
    def wikipedia(self, q, lang="vi", limit=5):
        return {"ok": True, "data": {"query": {"search": [{"title": "Đà Nẵng" if lang == "vi" else "Da Nang"}]}}}
    def wikipedia_page(self, title, lang="vi"):
        return {"ok": True, "data": {"extract": "Đà Nẵng là thành phố ven biển ở miền Trung Việt Nam với nhiều giá trị du lịch."}}
    def osm_search(self, q, limit=5):
        return {"ok": True, "data": {"results": [{"name": "Da Nang", "display_name": "Da Nang, Vietnam"}]}}

class FakeImage:
    def resolve(self, *args, **kwargs):
        return {"ok": False, "confidence": "NONE"}


def test_smart_acquisition_builds_multisource_reference_profile(monkeypatch):
    acq=SmartKnowledgeAcquirer(FakeAdapter())
    monkeypatch.setattr(acq, "image_resolver", FakeImage())
    out=acq.acquire("Đà Nẵng")
    assert out["ok"] is True
    p=out["profile"]
    assert p["wikipedia"]["vi_extract"]
    assert "Wikipedia tiếng Việt" in p["sources"]
    assert "OpenStreetMap" in p["sources"]
    assert p["status"] in {"REFERENCE", "CANDIDATE"}


def test_sync_workflow_and_cache_contract():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    workflow=(root/".github/workflows/hdvia-open-data-agent.yml").read_text(encoding="utf-8")
    assert "scripts_smart_knowledge_sync.py" in workflow
    cache=root/"data/warehouse/smart_knowledge_cache.json"
    assert cache.exists()
    assert "REFERENCE_ONLY" in cache.read_text(encoding="utf-8")


def test_topic_aware_acquisition_collects_missing_domains(monkeypatch):
    acq=SmartKnowledgeAcquirer(FakeAdapter())
    monkeypatch.setattr(acq, "image_resolver", FakeImage())
    out=acq.acquire("Đà Nẵng", domains=["history", "food"])
    assert out["ok"] is True
    blocks=out["profile"]["knowledge_blocks"]
    assert {b["domain"] for b in blocks} == {"history", "food"}
    assert all(b["extract"] for b in blocks)
