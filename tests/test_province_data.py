import json
from pathlib import Path

from province_data import PROVINCES_2025, resolve_province


def test_34_province_catalog_2025():
    assert len(PROVINCES_2025) == 34
    assert len({p["code"] for p in PROVINCES_2025}) == 34
    assert len({p["slug"] for p in PROVINCES_2025}) == 34


def test_official_key_locations_and_mergers():
    assert resolve_province("Đà Nẵng")["code"] == "48"
    assert "Quảng Nam" in resolve_province("Đà Nẵng")["formed_from"]
    assert resolve_province("Hội An")["slug"] == "da-nang"
    assert resolve_province("Quảng Bình")["slug"] == "quang-tri"
    assert resolve_province("Kiên Giang")["slug"] == "an-giang"


def test_catalog_source_and_effective_date():
    p=Path("data/province_catalog_2025.json")
    d=json.loads(p.read_text(encoding="utf-8"))
    assert d["effective_date"] == "2025-07-01"
    assert "Nghị quyết 202/2025/QH15" in d["source"]
    assert d["count"] == 34
