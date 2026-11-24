import os
from external_gateway import ExternalDataGateway

def test_gateway_status_never_exposes_secrets(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY","secret-value")
    s=ExternalDataGateway().status()
    raw=str(s)
    assert "secret-value" not in raw
    assert s["providers"]["openai"]["enabled"] is True

def test_gateway_has_provider_contracts(monkeypatch):
    for k in ("GOOGLE_MAPS_API_KEY","GOOGLE_CSE_API_KEY","GOOGLE_CSE_CX","YOUTUBE_API_KEY","META_ACCESS_TOKEN","OPENAI_API_KEY","GEMINI_API_KEY","ANTHROPIC_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    p=ExternalDataGateway().status()["providers"]
    assert set(p) == {"google_places","google_cse","youtube","meta_graph","openai","gemini","anthropic"}
    assert all(v["enabled"] is False for v in p.values())

def test_meta_path_contract(monkeypatch):
    monkeypatch.setenv("META_ACCESS_TOKEN","x")
    import external_gateway
    seen={}
    def fake(method,url,**kwargs):
        seen.update(method=method,url=url,params=kwargs.get("params")); return {"id":"1"}
    monkeypatch.setattr(external_gateway,"_request",fake)
    out=ExternalDataGateway().meta_graph_get("PAGE_ID",{"fields":"id,name"})
    assert out["provider"]=="meta_graph"
    assert seen["url"].endswith("/v27.0/PAGE_ID")
    assert seen["params"]["access_token"]=="x"
