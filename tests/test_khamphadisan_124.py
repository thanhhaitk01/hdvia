from pathlib import Path
import json
from knowledge_layer import search_knowledge

ROOT=Path(__file__).resolve().parents[1]

def test_khamphadisan_reference_warehouse_loaded():
    p=ROOT/'data'/'warehouse'/'khamphadisan_seed_2026.json'
    d=json.loads(p.read_text(encoding='utf8'))
    assert d['version']=='1.24.0'
    assert len(d['records']) >= 8
    assert all(r['source'].startswith('http') for r in d['records'])

def test_editorial_reference_is_retrievable_for_place_questions():
    hits=search_knowledge('Cầu ngói Thanh Toàn', limit=5)
    assert any('Thanh Toàn' in (h.get('title') or '') for h in hits)
    hits=search_knowledge('Ký Ức Hội An', limit=5)
    assert any('Ký Ức Hội An' in (h.get('title') or '') for h in hits)

def test_kpd_records_are_reference_not_verified_fact():
    hits=search_knowledge('Trà Quế', limit=5)
    assert any(h.get('status') in ('REFERENCE','DISCOVERY_SOURCE','SOURCE_INDEX') for h in hits)
