import unittest
from unittest.mock import patch
import official_source_discovery as d

class TestOfficialSourceDiscovery(unittest.TestCase):
    @patch.dict(d.os.environ, {}, clear=True)
    def test_is_credential_gated(self):
        self.assertEqual(d.discover_official_sources("Chùa Cầu"), [])

    def test_domain_filter(self):
        self.assertTrue(d._allowed("https://dt.gov.vn/applications/tourism"))
        self.assertTrue(d._allowed("https://nentangso.vietnamtourism.gov.vn/x"))
        self.assertFalse(d._allowed("https://example.com/x"))

if __name__ == "__main__":
    unittest.main()
