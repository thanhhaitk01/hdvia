import json
import knowledge_self_healing as mod


class FakeAcquirer:
    def acquire(self, name, **kwargs):
        return {"ok": True, "profile": {
            "name": name,
            "sources": ["Wikipedia tiếng Việt"],
            "knowledge_blocks": [
                {"domain": "history", "title": f"{name} — lịch sử", "extract": "Dữ liệu lịch sử tham khảo."},
                {"domain": "food", "title": f"{name} — ẩm thực", "extract": "Dữ liệu ẩm thực tham khảo."},
            ],
            "wikipedia": {"vi_extract": "Mô tả tham khảo."},
            "acquired_at": "2026-11-27T00:00:00Z", "research_depth": "DEEP",
        }}


def test_self_healing_detects_gap_acquires_and_persists(monkeypatch, tmp_path):
    cache=tmp_path / "smart_knowledge_cache.json"
    monkeypatch.setattr(mod, "CACHE", cache)
    engine=mod.KnowledgeSelfHealingEngine(FakeAcquirer())
    first=engine.ensure("Hà Tĩnh", domain="HISTORY")
    assert first["ok"] is True
    assert first["status"] == "ACQUIRED"
    assert first["changed"] is True
    saved=json.loads(cache.read_text(encoding="utf-8"))
    assert "hã tĩnh" not in saved.get("profiles", {})
    assert "hà tĩnh" in saved.get("profiles", {})
    second=engine.ensure("Hà Tĩnh", domain="HISTORY")
    assert second["ok"] is True
    assert second["status"] == "CACHE"
    assert second["changed"] is False


def test_reference_lines_are_answer_safe():
    lines=mod.reference_lines({"name":"Đà Nẵng","knowledge_blocks":[{"domain":"food","title":"Ẩm thực","extract":"Mì Quảng là món ăn tham khảo."}]},domain="FOOD")
    assert lines and "Mì Quảng" in lines[0]
