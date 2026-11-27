from ai_gateway import AIGateway, AIProvider
from self_update_engine import SelfUpdateEngine

def test_gateway_reports_unconfigured_provider():
    g=AIGateway([AIProvider("gemini","https://example.invalid","MISSING_KEY","MISSING_MODEL","gemini-2.5-flash-lite",enabled=True)])
    r=g.ask("test")
    assert r["ok"] is False
    assert r["status"] == "NO_PROVIDER_AVAILABLE"

def test_self_update_candidate_is_not_published():
    class G:
        def ask(self,*a,**k): return {"ok":True,"result":{"text":"{}"}}
        def status(self): return {"providers":[]}
    e=SelfUpdateEngine(G())
    c=e.candidate_from_external(question="Thời tiết Hội An?",place="Hội An",domain="weather",content="Nguồn thông tin cần kiểm chứng đủ dài cho pipeline.",source_url="https://example.org/source")
    assert c["status"] == "CANDIDATE"
    assert c["publication_policy"] == "REVIEW_BEFORE_PUBLISH"

def test_status_contains_safe_mode():
    class G:
        def status(self): return {"providers":[]}
    e=SelfUpdateEngine(G())
    h=e.health()
    assert h["mode"] == "controlled_self_update"
    assert h["publish_policy"] == "review_or_validation_required"
