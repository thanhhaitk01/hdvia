import unittest
from travel_intelligence_brain import build_travel_brain
from conversation_engine import ConversationIntelligenceEngine

class Test1301ReasoningHardening(unittest.TestCase):
    def test_explicit_hdV_context_becomes_decision_input(self):
        q = "Tôi dẫn đoàn khách quốc tế lớn tuổi ở Cố đô Hoa Lư, nếu mưa thì nên đổi thứ tự và Plan B thế nào?"
        r = build_travel_brain("Cố đô Hoa Lư", query=q, profile={"sources": ["HDVIA Destination Catalog"]},
                               weather=[{"rain":80,"wind":20,"tmax":34}])
        self.assertTrue(r["guide_context"]["guest_profile"]["international"])
        self.assertTrue(r["guide_context"]["guest_profile"]["elderly"])
        self.assertIn("backup", r["guide_context"]["guide_objectives"])
        self.assertTrue(r["guide_decision"]["plan_b"])

    def test_conflict_changes_reasoning_status(self):
        r = build_travel_brain("Lễ hội Hoa Lư", profile={"evidence":[
            {"subject":"festival_date","source":"A","fact":"10/3","impact":"DATE"},
            {"subject":"festival_date","source":"B","fact":"12/3","impact":"DATE"},
        ]})
        self.assertEqual(r["reasoning"]["status"], "CONFLICT_REQUIRES_VERIFICATION")
        self.assertGreaterEqual(r["reasoning"]["conflict_count"], 1)

    def test_query_keeps_multiple_dimensions(self):
        e = ConversationIntelligenceEngine()
        q = "Tôi là HDV dẫn khách quốc tế tham quan Hoa Lư, hãy phân tích lịch sử, thời tiết, rủi ro, thuyết minh và Plan B nếu mưa."
        c = e.answer(q)
        self.assertTrue(set(["HISTORY", "WEATHER", "RISK", "GUIDE_SCRIPT", "PLAN_B"]).intersection(c["intents"]))
        self.assertIn("requested_dimensions", c["query_contract"])

if __name__ == "__main__":
    unittest.main()
