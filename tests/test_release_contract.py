import unittest
from pathlib import Path
import release_qa

class TestReleaseContract(unittest.TestCase):
    def test_expected_release_version(self):
        self.assertEqual(release_qa.VERSION, release_qa.EXPECTED)

if __name__ == "__main__":
    unittest.main()
