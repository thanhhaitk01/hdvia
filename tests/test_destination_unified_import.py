from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_app_imports_by_name_for_unified_destination_context():
    src=(ROOT/'app.py').read_text(encoding='utf-8')
    assert 'from destination_catalog import DESTINATIONS, BY_SLUG, BY_NAME' in src

def test_destination_catalog_exposes_by_name():
    src=(ROOT/'destination_catalog.py').read_text(encoding='utf-8')
    assert 'BY_NAME = {d["name"].lower(): d for d in DESTINATIONS}' in src
