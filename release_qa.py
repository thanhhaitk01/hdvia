"""HDVIA 1.25.4 release contract checks.

Fast, deterministic checks for the release bundle. Network calls are intentionally
not made here; provider connectivity is covered by the existing smoke test.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
EXPECTED = "1.25.4.4-world-qa-image-rendering"


def fail(msg: str) -> None:
    raise SystemExit(f"RELEASE_QA_FAIL: {msg}")


def main() -> None:
    if VERSION != EXPECTED:
        fail(f"VERSION={VERSION!r}, expected {EXPECTED!r}")

    runtime_files = [
        ROOT / "VERSION",
        ROOT / "app.py",
        ROOT / "api_adapters.py",
        ROOT / "image_entity_resolution.py",
        ROOT / "world_acquisition_engine.py",
    ]
    for path in runtime_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if EXPECTED not in text:
            fail(f"runtime version missing from {path.name}")

    forbidden_artifacts = {".pyc", ".pyo", ".DS_Store"}
    forbidden_dirs = {"__pycache__", ".pytest_cache"}
    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix in forbidden_artifacts:
            fail(f"forbidden artifact: {path.relative_to(ROOT)}")
        if path.is_dir() and path.name in forbidden_dirs:
            fail(f"forbidden directory: {path.relative_to(ROOT)}")

    secret_patterns = [
        re.compile(r'(?i)\b(?:GOOGLE|FACEBOOK|ZALO|GEMINI|OPENAI)[A-Z0-9_]*_SECRET\s*=\s*[^$\s][^\n#]*'),
        re.compile(r'(?i)\b(?:API_KEY|ACCESS_TOKEN|SECRET_KEY)\s*=\s*["\']?(?!\s*$)[A-Za-z0-9_\-]{20,}'),
    ]
    scan_ext = {".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yml", ".yaml", ".env", ".md"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in scan_ext:
            continue
        if path.name in {".env.example"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in secret_patterns:
            if pattern.search(text):
                fail(f"possible bundled secret in {path.relative_to(ROOT)}")

    print(f"RELEASE_QA_PASS: {EXPECTED}")
    print("runtime_version_sync=PASS")
    print("forbidden_artifacts=PASS")
    print("bundled_secret_scan=PASS")


if __name__ == "__main__":
    main()
