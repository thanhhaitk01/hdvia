import unittest
from travel_intelligence_brain import build_travel_brain
from hdv_experience_memory import build_experience_memory
from guide_route_decision import evaluate_route_time
from source_conflict_resolution import detect_conflicts

class TestHDVExperienceDepth(unittest.TestCase):
    def test_experience_memory_matches_conditions(self):
        r=build_experience_memory("RELIGIOUS_SITE",{"max_temperature_c":36},{"elderly":True},{})
        self.assertEqual(r["matched_scenarios"],1)
        self.assertTrue(r["lessons"])

    def test_route_time_detects_overrun(self):
        r=evaluate_route_time("ATTRACTION",{"time_remaining_minutes":90,"travel_minutes":35,"visit_minutes":50,"buffer_minutes":15},{},{})
        self.assertEqual(r["status"],"ROUTE_DECISION_READY")
        self.assertTrue(r["plan_b"])

    def test_conflict_guard(self):
        r=detect_conflicts([
            {"subject":"festival_date","source":"A","fact":"10/3"},
            {"subject":"festival_date","source":"B","fact":"12/3"},
        ])
        self.assertTrue(r["has_conflict"])
        self.assertEqual(len(r["conflicts"]),1)

    def test_brain_exposes_depth_layers(self):
        r=build_travel_brain("Lễ hội Hoa Lư",profile={
            "operational":{"time_remaining_minutes":60,"travel_minutes":20,"visit_minutes":50,"buffer_minutes":10},
            "guest_profile":{"elderly":True},
            "evidence":[{"subject":"festival_date","source":"A","fact":"10/3"},{"subject":"festival_date","source":"B","fact":"12/3"}]
        },weather=[{"rain":80,"wind":35,"tmax":36,"weather_code":95}])
        self.assertIn("experience_memory",r)
        self.assertIn("route_time_decision",r)
        self.assertTrue(r["source_conflicts"]["has_conflict"])
        self.assertTrue(r["guide_decision"]["plan_b"])

if __name__ == '__main__': unittest.main()
