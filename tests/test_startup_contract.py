from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]

def test_app_imports_timezone_for_now_helper():
    src = (ROOT / "app.py").read_text(encoding="utf8")
    tree = ast.parse(src)
    imports_datetime = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "datetime":
            imports_datetime.extend(alias.name for alias in node.names)
    assert "datetime" in imports_datetime
    assert "timezone" in imports_datetime

def test_now_helper_does_not_reference_missing_timezone():
    src = (ROOT / "app.py").read_text(encoding="utf8")
    assert "datetime.now(timezone.utc)" in src
