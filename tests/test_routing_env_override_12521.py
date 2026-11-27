import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_new_routing_flag_overrides_legacy_false(monkeypatch):
    monkeypatch.setenv("HDVIA_LIVE_ROUTING", "false")
    monkeypatch.setenv("HDVIA_ENABLE_LIVE_ROUTING", "true")
    from api_adapters import OpenAPIAdapter
    adapter = OpenAPIAdapter()
    assert adapter.live_routing is True


def test_legacy_routing_flag_still_works(monkeypatch):
    monkeypatch.delenv("HDVIA_ENABLE_LIVE_ROUTING", raising=False)
    monkeypatch.setenv("HDVIA_LIVE_ROUTING", "true")
    from api_adapters import OpenAPIAdapter
    adapter = OpenAPIAdapter()
    assert adapter.live_routing is True


def test_routing_remains_disabled_by_default(monkeypatch):
    monkeypatch.delenv("HDVIA_ENABLE_LIVE_ROUTING", raising=False)
    monkeypatch.delenv("HDVIA_LIVE_ROUTING", raising=False)
    from api_adapters import OpenAPIAdapter
    adapter = OpenAPIAdapter()
    assert adapter.live_routing is False
