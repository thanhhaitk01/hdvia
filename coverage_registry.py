"""Vietnam tourism coverage registry for HDVIA Journey/Conversation AI.

This registry deliberately separates recognition from verified knowledge. A place can
be recognized as a tourism hub or landmark without HDVIA pretending it has enough
curated facts to answer detailed questions about it.
"""
from province_data import PROVINCES_2025
from functools import lru_cache
from destination_catalog import DESTINATIONS

CATEGORIES = [
    "điểm du lịch", "địa danh", "di tích lịch sử", "khu vui chơi giải trí",
    "làng nghề", "bảo tàng", "thắng cảnh", "tâm linh", "biển đảo",
    "thiên nhiên", "văn hóa", "ẩm thực", "cộng đồng", "nghỉ dưỡng",
    "mua sắm", "trải nghiệm", "sự kiện"
]

def _norm(s):
    import re
    return " ".join(re.sub(r"[^\wÀ-ỹĐđ→>\- ]+", " ", str(s or "").lower()).split())

RECOGNIZED_PLACES = {}
for p in PROVINCES_2025:
    province = p.get("name", "")
    for raw in [province, *(p.get("aliases") or []), *(p.get("tourism_hubs") or [])]:
        key = _norm(raw)
        if key:
            RECOGNIZED_PLACES.setdefault(key, {"name": raw, "province": province,
                "region": p.get("region"), "kind": "tourism-hub"})
for d in DESTINATIONS:
    for raw in [d.get("name"), *(d.get("highlights") or [])]:
        key = _norm(raw)
        if key:
            RECOGNIZED_PLACES[key] = {"name": raw, "province": d.get("name"),
                "region": d.get("region"), "kind": "destination" if raw == d.get("name") else "landmark",
                "catalog": d}

# High-frequency guide aliases that are commonly used without the full catalog name.
# Recognition remains separate from detailed fact coverage.
_LANDMARK_ALIASES = {
    "bà nà": "Bà Nà Hills",
    "ba na": "Bà Nà Hills",
    "bana": "Bà Nà Hills",
    "linh ứng": "Chùa Linh Ứng Sơn Trà",
    "linh ung": "Chùa Linh Ứng Sơn Trà",
    "chùa linh ứng": "Chùa Linh Ứng Sơn Trà",
    "chua linh ung": "Chùa Linh Ứng Sơn Trà",
}
for _alias, _canonical in _LANDMARK_ALIASES.items():
    _a = _norm(_alias); _c = _norm(_canonical)
    _item = dict(RECOGNIZED_PLACES.get(_c, {
        "name": _canonical, "province": "Đà Nẵng", "region": "Miền Trung", "kind": "landmark"
    }))
    RECOGNIZED_PLACES[_c] = _item
    RECOGNIZED_PLACES[_a] = dict(_item)

_FIRST_TOKEN_INDEX = {}
for _key in RECOGNIZED_PLACES:
    _FIRST_TOKEN_INDEX.setdefault(_key.split()[0], []).append(_key)
for _token in _FIRST_TOKEN_INDEX:
    _FIRST_TOKEN_INDEX[_token].sort(key=len, reverse=True)

@lru_cache(maxsize=4096)
def resolve_known_place(query):
    q = _norm(query)
    hits=[]; seen=set()
    # Restrict substring checks to names whose first token is actually present.
    tokens=set(q.split())
    candidate_keys=[]
    for token in tokens:
        candidate_keys.extend(_FIRST_TOKEN_INDEX.get(token, ()))
    for key in sorted(set(candidate_keys), key=len, reverse=True):
        if key and key in q and key not in seen:
            item=dict(RECOGNIZED_PLACES[key]); hits.append(item); seen.add(key)
            if len(hits)>=8: break
    return hits
