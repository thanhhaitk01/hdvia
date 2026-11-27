import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from api_adapters import OpenAPIAdapter, API_LAYER_VERSION

class TestAPIConnectivity(unittest.TestCase):
    def setUp(self):
        self.a = OpenAPIAdapter()

    def test_version(self):
        self.assertEqual(API_LAYER_VERSION, "1.25.2.4-api-connectivity-live-data-hardened")

    def test_cache_policy_present(self):
        self.assertGreaterEqual(self.a.cache_ttls["weather"], 0)
        self.assertGreaterEqual(self.a.cache_ttls["image"], 0)
        self.assertGreaterEqual(self.a.cache_ttls["route"], 0)

    def test_status_has_image(self):
        status = self.a.status()
        self.assertIn("image", status["providers"])
        self.assertIn("cache_ttls_seconds", status)

    def test_image_response_contract(self):
        result = self.a.image("Chùa Cầu Hội An")
        self.assertIn("ok", result)
        self.assertIn("freshness", result)

    def test_live_smoke(self):
        # Network smoke test; skip explicitly when CI has no outbound network.
        result = self.a.probe_connectivity()
        self.assertIn("summary", result)
        self.assertEqual(result["summary"]["total"], 10)
        self.assertIn("image", result["checks"])

if __name__ == "__main__":
    unittest.main()
