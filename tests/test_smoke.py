import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_required_files_exist():
    for name in ("app.py", "oauth.py", "requirements.txt", "vercel.json", "templates", "static", "journey_engine"):
        assert (ROOT / name).exists(), name


def test_requirements_include_authlib():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    assert "authlib==1.6.5" in requirements
    assert "flask==3.1.0" in requirements
