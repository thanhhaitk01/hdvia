import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_vercel_uses_flask_zero_config():
    cfg = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    assert cfg.get("version") == 2
    assert "builds" not in cfg
    assert "routes" not in cfg


def test_flask_entrypoint_is_exported_at_root():
    src = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "app=Flask(__name__)" in src


def test_app_module_name_does_not_shadow_root_entrypoint():
    # Vercel/WSGI imports must resolve the root app.py entrypoint, not a sibling
    # package named app.
    assert (ROOT / "app.py").is_file()
    assert not (ROOT / "app").is_dir()
