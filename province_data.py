import json, os
from functools import lru_cache

BASE=os.path.dirname(__file__)
DATA_FILE=os.path.join(BASE,'data','province_catalog_2025.json')

@lru_cache(maxsize=1)
def load_provinces():
    with open(DATA_FILE,'r',encoding='utf-8') as f:
        return json.load(f)

PROVINCES_2025=load_provinces()["provinces"]
BY_PROVINCE_SLUG={p['slug']:p for p in PROVINCES_2025}
BY_PROVINCE_NAME={p['name'].lower():p for p in PROVINCES_2025}
BY_PROVINCE_ALIAS={a.lower():p for p in PROVINCES_2025 for a in p.get('aliases',[])}

def resolve_province(value):
    if not value: return None
    key=str(value).strip().lower()
    return BY_PROVINCE_SLUG.get(key) or BY_PROVINCE_NAME.get(key) or BY_PROVINCE_ALIAS.get(key)
