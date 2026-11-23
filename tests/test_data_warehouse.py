import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from warehouse import COLLECTIONS, warehouse_schema, warehouse_seed, normalize_record

def test_warehouse_schema_has_all_collections():
    schema = warehouse_schema()['collections']
    assert set(COLLECTIONS) <= set(schema)
    for kind in COLLECTIONS:
        assert schema[kind]['required']

def test_seed_shape():
    seed = warehouse_seed()
    assert set(COLLECTIONS) <= set(seed)
    assert all(isinstance(seed[k], list) for k in COLLECTIONS)

def test_destination_record_validation():
    row = normalize_record('destinations', {'slug':'hue','name':'Huế','province':'Huế','type':'Di sản','overview':'Cố đô'})
    assert row['name'] == 'Huế'
    assert row['updated_at'].endswith('Z')

def test_invalid_record_is_rejected():
    try:
        normalize_record('knowledge', {'title':'Thiếu nội dung'})
        assert False
    except ValueError as exc:
        assert 'Thiếu trường bắt buộc' in str(exc)
