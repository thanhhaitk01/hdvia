import unittest
from image_entity_resolution import VerifiedImageResolver
from media_warehouse import build_media_record


def page(title, url, desc):
    return {"title": title, "imageinfo": [{"thumburl": url, "extmetadata": {"ImageDescription": {"value": desc}, "LicenseShortName": {"value": "CC BY-SA"}}}]}


class Adapter:
    def wikidata_entity(self, entity_id):
        return {"ok": True, "data": {"entities": {entity_id: {"claims": {}}}}}
    def image(self, name):
        return {"ok": True, "data": {"query": {"pages": {"1": page("File:Golden Bridge Ba Na Hills.jpg", "https://x/wrong.jpg", "Golden Bridge Ba Na Hills")}}}}
    def openverse_image(self, name, limit=5):
        return {"ok": True, "data": {"results": [{"thumbnail": "https://x/right.jpg", "title": "Japanese Bridge Hoi An", "description": "Japanese Bridge, Hoi An, Vietnam", "creator": "A", "license": "cc-by", "foreign_landing_url": "https://openverse.org/x"}]}}
    def image_geosearch(self, lat, lon, radius_m=5000, limit=10):
        return {"ok": True, "data": {"query": {"pages": {}}}}


class TestSixLayerMediaFusion(unittest.TestCase):
    def test_openverse_candidate_can_verify_when_commons_is_wrong(self):
        r = VerifiedImageResolver(Adapter()).resolve("Chùa Cầu Hội An", lat=15.8777, lon=108.3268)
        self.assertTrue(r["ok"])
        self.assertEqual(r["source"], "openverse")
        self.assertIn("license_metadata_present", r["evidence"]["reasons"])

    def test_media_record_has_provenance(self):
        rec = build_media_record(entity_id="Q1", entity_name="Chùa Cầu", candidate={"url":"https://x/a.jpg","_source":"openverse","license":"cc-by"}, score=91, confidence="HIGH", evidence={"reasons":["entity"]})
        self.assertEqual(rec["status"], "VERIFIED")
        self.assertEqual(rec["license"], "cc-by")
        self.assertTrue(rec["media_id"].startswith("media-"))

if __name__ == "__main__":
    unittest.main()
