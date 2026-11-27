import unittest
from travel_intelligence_brain import VERSION, classify_object, build_travel_brain

class TestTravelIntelligenceBrain(unittest.TestCase):
    def test_festival_classification(self):
        r = classify_object("Lễ hội Cầu Ngư")
        self.assertEqual(r["type"], "FESTIVAL")

    def test_religious_site_classification(self):
        r = classify_object("Đền Ngọc Sơn")
        self.assertEqual(r["type"], "RELIGIOUS_SITE")

    def test_food_classification(self):
        r = classify_object("bánh tráng Túy Loan")
        self.assertEqual(r["type"], "FOOD")

    def test_brain_outputs_guide_actions(self):
        r = build_travel_brain(
            "Đền Ngọc Sơn",
            profile={"sources":["Wikipedia tiếng Việt"],"confidence":"MEDIUM","status":"REFERENCE","coordinates":{"lat":21.028,"lon":105.852}},
            weather=[{"rain":80,"wind":35,"tmax":36,"weather_code":95}],
            admin={"commune":"Hoàn Kiếm","province":"Hà Nội"},
        )
        self.assertEqual(r["version"], VERSION)
        self.assertEqual(r["object"]["type"], "RELIGIOUS_SITE")
        self.assertTrue(r["research_plan"])
        self.assertTrue(r["operational_actions"])
        self.assertEqual(r["local_context"]["commune"], "Hoàn Kiếm")
        self.assertTrue(any("thời tiết" in x.lower() or "mưa" in x.lower() for x in r["research_plan"] + r["operational_actions"]))

if __name__ == "__main__":
    unittest.main()
