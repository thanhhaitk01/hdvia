import unittest
from entity_resolution import EntityResolver

class Adapter:
    def wikidata(self, query, limit=5):
        return {"ok": True, "data": {"search": [{"id":"Q1091054","label":"Japanese Bridge","description":"Japanese Bridge, Hoi An, Vietnam"}]}}

class TestEntityResolutionAliases(unittest.TestCase):
    def test_aliases_resolve_same_entity(self):
        resolver=EntityResolver(Adapter())
        names=["Chùa Cầu", "Chùa Cầu Hội An", "Cầu Nhật Bản Hội An", "Japanese Bridge"]
        ids=[resolver.resolve(n)["wikidata"]["id"] for n in names]
        self.assertEqual(ids, ["Q1091054"]*4)

    def test_unknown_does_not_invent_entity(self):
        class Empty(Adapter):
            def wikidata(self, query, limit=5): return {"ok": True, "data": {"search": []}}
        r=EntityResolver(Empty()).resolve("Địa điểm không tồn tại trong bộ test")
        self.assertEqual(r["confidence"], "UNRESOLVED")
        self.assertIsNone(r["wikidata"])

if __name__ == "__main__": unittest.main()
