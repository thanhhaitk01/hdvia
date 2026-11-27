import unittest
from image_entity_resolution import VerifiedImageResolver


def page(title, url, desc, lat=None, lon=None):
    meta = {"ImageDescription": {"value": desc}}
    if lat is not None:
        meta["GPSLatitude"] = {"value": str(lat)}
    if lon is not None:
        meta["GPSLongitude"] = {"value": str(lon)}
    return {"title": title, "imageinfo": [{"thumburl": url, "extmetadata": meta}]}


class FakeAdapter:
    def wikidata_entity(self, entity_id):
        claim = {"mainsnak": {"datavalue": {"value": "Japanese Bridge in Hoi An.jpg"}}}
        return {"ok": True, "data": {"entities": {
            entity_id: {"claims": {"P18": [claim]}}
        }}}

    def image_exact(self, title):
        p = page("File:" + title, "https://commons.example/exact.jpg",
                 "Japanese Bridge, Hoi An, Vietnam", 15.8777, 108.3268)
        return {"ok": True, "data": {"query": {"pages": {"1": p}}}}

    def image(self, name):
        p1 = page("File:Golden Bridge Ba Na Hills.jpg",
                  "https://commons.example/wrong.jpg",
                  "Golden Bridge, Ba Na Hills, Vietnam")
        p2 = page("File:Japanese Bridge Hoi An.jpg",
                  "https://commons.example/right.jpg",
                  "Japanese Bridge, Hoi An, Vietnam", 15.8777, 108.3268)
        return {"ok": True, "data": {"query": {"pages": {"2": p1, "3": p2}}}}

    def image_geosearch(self, lat, lon, radius_m=5000, limit=10):
        return {"ok": True, "data": {"query": {"pages": {}}}}


class TestVerifiedImageResolution(unittest.TestCase):
    def test_wikidata_p18_wins_and_is_verified(self):
        r = VerifiedImageResolver(FakeAdapter()).resolve(
            "Chùa Cầu Hội An",
            entity={"wikidata": {"id": "Q1091054", "label": "Japanese Bridge"}},
            lat=15.8777, lon=108.3268,
        )
        self.assertTrue(r["ok"])
        self.assertEqual(r["source"], "wikidata_p18")
        self.assertEqual(r["entity_id"], "Q1091054")
        self.assertGreaterEqual(r["score"], 88)

    def test_wrong_only_candidate_is_rejected(self):
        class WrongOnly(FakeAdapter):
            def wikidata_entity(self, entity_id):
                return {"ok": True, "data": {"entities": {entity_id: {"claims": {}}}}}
            def image(self, name):
                p = page("File:Golden Bridge Ba Na Hills.jpg",
                         "https://commons.example/wrong.jpg",
                         "Golden Bridge, Ba Na Hills")
                return {"ok": True, "data": {"query": {"pages": {"1": p}}}}
        r = VerifiedImageResolver(WrongOnly()).resolve(
            "Chùa Cầu Hội An",
            entity={"wikidata": {"id": "Q1091054"}},
            lat=15.8777, lon=108.3268,
        )
        self.assertFalse(r["ok"])
        self.assertIn(r["reason"],
                      {"candidate_below_verified_threshold", "no_verified_candidate"})

    def test_no_guess_when_unverified(self):
        class Empty(FakeAdapter):
            def wikidata_entity(self, entity_id):
                return {"ok": True, "data": {"entities": {entity_id: {"claims": {}}}}}
            def image(self, name):
                return {"ok": True, "data": {"query": {"pages": {}}}}
        r = VerifiedImageResolver(Empty()).resolve("Địa điểm chưa xác định")
        self.assertFalse(r["ok"])
        self.assertEqual(r["confidence"], "NONE")


if __name__ == "__main__":
    unittest.main()
