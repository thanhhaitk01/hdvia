import json, os
from datetime import datetime, timezone

BASE = os.path.dirname(__file__)
WAREHOUSE_DIR = os.path.join(BASE, 'data', 'warehouse')
SCHEMA_FILE = os.path.join(WAREHOUSE_DIR, 'schema.json')
SEED_FILE = os.path.join(WAREHOUSE_DIR, 'seed.json')

COLLECTIONS = ('destinations', 'knowledge', 'guide_scripts', 'experiences', 'media')

def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')

def load_json(path, default):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def warehouse_schema():
    return load_json(SCHEMA_FILE, {'collections': {}})

def warehouse_seed():
    return load_json(SEED_FILE, {name: [] for name in COLLECTIONS})

def normalize_record(kind, payload):
    if kind not in COLLECTIONS:
        raise ValueError('Loại dữ liệu không hợp lệ.')
    required = warehouse_schema().get('collections', {}).get(kind, {}).get('required', [])
    data = {str(k): v for k, v in payload.items() if str(k) not in ('csrf_token', 'kind')}
    missing = [key for key in required if not str(data.get(key, '')).strip()]
    if missing:
        raise ValueError('Thiếu trường bắt buộc: ' + ', '.join(missing))
    data['updated_at'] = utc_now()
    return data
