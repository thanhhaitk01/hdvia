import unittest
from datetime import datetime, timezone, timedelta
from six_layer_data_fusion import VERSION, LAYERS, layer_health, build_record, freshness

class TestSixLayerDataFusion(unittest.TestCase):
    def test_has_exactly_six_layers(self):
        self.assertEqual(len(LAYERS), 6)
        self.assertEqual(layer_health()["status"], "PASS")
        self.assertEqual(layer_health()["version"], VERSION)

    def test_discovered_external_is_candidate(self):
        r = build_record(source_id="wikidata", payload={"name":"Chùa Cầu"}, entity={"confidence":"HIGH"})
        self.assertEqual(r["status"], "CANDIDATE")
        self.assertEqual(r["freshness"], "FRESH")
        self.assertEqual(r["layer_trace"], list(LAYERS))

    def test_review_required_sources_cannot_auto_verify(self):
        r = build_record(source_id="open_data_tourism", payload={"name":"Chùa Cầu"}, entity={"confidence":"HIGH"}, human_verified=False)
        self.assertEqual(r["status"], "CANDIDATE")

    def test_human_verified_can_promote(self):
        r = build_record(source_id="open_data_tourism", payload={"name":"Chùa Cầu"}, entity={"confidence":"HIGH"}, human_verified=True)
        self.assertEqual(r["status"], "VERIFIED")

    def test_stale_expiry(self):
        past=(datetime.now(timezone.utc)-timedelta(days=1)).isoformat().replace('+00:00','Z')
        self.assertEqual(freshness(past), "STALE")

if __name__ == "__main__": unittest.main()
