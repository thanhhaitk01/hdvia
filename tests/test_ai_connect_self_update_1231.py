from ai_gateway import AIGateway, AIProvider
from self_update_engine import SelfUpdateEngine
from conversation_engine import ConversationIntelligenceEngine

def test_gateway_bounds_prompt_and_reports_unconfigured_provider():
    g=AIGateway([AIProvider("gemini","https://example.invalid","MISSING_KEY","MISSING_MODEL","gemini-2.5-flash-lite",enabled=True)])
    r=g.ask("x"*20000)
    assert not r["ok"] and r["status"] == "NO_PROVIDER_AVAILABLE"

def test_self_update_enrich_creates_candidate_without_publish():
    class G:
        def ask(self,*a,**k):
            return {"ok":True,"result":{"text":'{"gap":"thiếu dữ liệu","content":"Thông tin bổ sung cần kiểm chứng từ nguồn chính thức.","source_url":"https://example.org/source"}'}}
        def status(self): return {"providers":[]}
    r=SelfUpdateEngine(G()).enrich(question="Huế có gì mới?",place="Huế",domain="DESTINATION")
    assert r["ok"] and r["status"] == "CANDIDATE"
    assert r["candidate"]["publication_policy"] == "REVIEW_BEFORE_PUBLISH"

def test_conversation_enrichment_is_opt_in_and_scoped(monkeypatch):
    calls=[]
    def enrich(**kwargs): calls.append(kwargs); return {"ok":True,"candidate":{"content":"candidate"}}
    monkeypatch.setenv("HDVIA_AI_AUTO_ENRICH","1")
    r=ConversationIntelligenceEngine(enrich).answer("Một câu hỏi du lịch chưa có dữ liệu ở Huế")
    assert calls and r["knowledge_enrichment"]["ok"]

def test_conversation_does_not_delegate_weather_to_external_ai(monkeypatch):
    calls=[]
    def enrich(**kwargs): calls.append(kwargs); return {"ok":True,"candidate":{"content":"candidate"}}
    monkeypatch.setenv("HDVIA_AI_AUTO_ENRICH","1")
    ConversationIntelligenceEngine(enrich).answer("Ngày mai Huế có mưa không?")
    assert calls == []
