import unittest
from travel_intelligence_brain import build_travel_brain, VERSION
from travel_ontology import classify_multilabel

class TestHDVExperience(unittest.TestCase):
    def test_version(self):
        self.assertEqual(VERSION, "1.30.1-hdv-giau-kinh-nghiem")

    def test_multilabel_ontology(self):
        r=classify_multilabel("Lễ hội tại Cố đô Hoa Lư")
        self.assertIn("FESTIVAL", r["types"])
        self.assertIn("HERITAGE_SITE", r["types"])

    def test_story_brief_decision(self):
        r=build_travel_brain(
            "Cố đô Hoa Lư", query="lễ hội Hoa Lư",
            profile={"sources":["Khám Phá Di Sản"], "highlights":["di sản lịch sử"],
                     "related_entities":[{"name":"Đinh Tiên Hoàng","type":"PERSON","relation":"associated_with"}],
                     "guest_profile":{"elderly":True}},
            weather=[{"rain":80,"wind":35,"tmax":36,"weather_code":95}],
            admin={"commune":"Trường Yên","province":"Ninh Bình"})
        self.assertEqual(r["version"], VERSION)
        self.assertTrue(r["travel_story_graph"]["story_ready"])
        self.assertEqual(r["hdv_experience_brief"]["experience_level"], "HDV_GIAU_KINH_NGHIEM")
        self.assertTrue(r["guide_decision"]["actions"])
        self.assertTrue(r["guide_decision"]["plan_b"])

if __name__ == "__main__": unittest.main()
