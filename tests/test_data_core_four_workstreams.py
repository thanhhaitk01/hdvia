import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data_core import seed, graph_integrity_report, LearningPipeline
from data_core_bridge import DataCoreBridge
from copilot import CopilotEngine


def test_four_workstreams_core_graph_is_integrity_checked():
    report=graph_integrity_report(seed())
    assert report["ok"] is True
    assert report["counts"]["administrative"]==34
    assert report["counts"]["destinations"]>=10
    assert report["counts"]["knowledge"]>=10
    assert report["counts"]["experiences"]>=10
    assert report["counts"]["market"]>=10


def test_journey_bridge_uses_all_linked_domains_and_runtime_weather():
    class C:
        def execute(self,q,params):
            import json
            rows=[{"payload_json":json.dumps(x)} for x in seed().get(params[0],[])]
            class R:
                def fetchall(self): return rows
            return R()
        def close(self): pass
    bridge=DataCoreBridge(lambda:C())
    result=bridge.enrich_journey({
        "places":[{"name":"Đà Nẵng"},{"name":"Hội An"},{"name":"Huế"}],
        "weather":{"Đà Nẵng":[{"date":"2026-11-24","code":0}],"Hội An":[{"date":"2026-11-24","code":61}],"Huế":[{"date":"2026-11-24","code":63}]},
        "risk_map":{"Đà Nẵng":{"level":"LOW"},"Hội An":{"level":"MEDIUM"},"Huế":{"level":"HIGH"}}
    })
    counts=result["data_core"]["counts"]
    assert set(result["data_core"]["destination_ids"])=={"dst:da-nang","dst:hoi-an","dst:hue"}
    assert counts["administrative"]>=2 and counts["knowledge"]>=3 and counts["experiences"]>=3 and counts["market"]>=3
    assert counts["weather_risk"]>=6
    assert any(x.get("forecast_type")=="LIVE_JOURNEY" for x in result["data_context"]["weather_risk"])


def test_acquisition_pipeline_stays_candidate_until_review():
    p=LearningPipeline()
    item=p.ingest(kind="knowledge",payload={"title":"Nguồn mới","place":"Huế","content":"Nội dung đủ dài để kiểm tra provenance và quy trình candidate của HDVIA.","source":"https://example.gov.vn/a"},source="https://example.gov.vn/a",source_type="OFFICIAL_GOVERNMENT")
    assert item["status"]=="CANDIDATE"
    checked=p.validate(item)
    assert checked["status"]=="VALIDATED"
    assert p.review(checked,approved=False,reviewer="admin@example")["status"]=="REJECTED"
    checked=p.validate(item)
    assert p.review(checked,approved=True,reviewer="admin@example")["status"]=="PUBLISHED"


def test_copilot_reads_context_instead_of_only_returning_generic_text():
    graph=seed()
    result=CopilotEngine().compose(user={"role":"GUIDE"},journey={"title":"Đà Nẵng Hội An Huế"},question="Tôi cần chuẩn bị gì?",data_context=graph)
    assert result["context"]["data_core_linked"] is True
    assert result["context"]["data_core_counts"]["destinations"]>=10
    assert "Đà Nẵng" in result["answer"] or "Huế" in result["answer"]
    assert result["recommendations"]
