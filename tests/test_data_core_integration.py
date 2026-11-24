import os,sys
sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
from data_core_bridge import DataCoreBridge
from data_core import seed

def test_bridge_resolves_multi_stop_journey_to_linked_domains():
    class C:
        def execute(self, q, params):
            kind=params[0]
            rows=[{"payload_json":__import__('json').dumps(x)} for x in seed().get(kind,[])]
            class R:
                def fetchall(self): return rows
            return R()
        def close(self): pass
    b=DataCoreBridge(lambda:C())
    result=b.enrich_journey({"title":"Đà Nẵng - Hội An - Huế","places":[{"name":"Đà Nẵng"},{"name":"Hội An"},{"name":"Huế"}]})
    assert result["data_core"]["linked"] is True
    assert set(result["data_core"]["destination_ids"])=={"dst:da-nang","dst:hoi-an","dst:hue"}
    assert result["data_core"]["counts"]["knowledge"] >= 3
    assert result["data_core"]["counts"]["experiences"] >= 2
    assert result["data_core"]["counts"]["market"] >= 2
    assert result["data_core"]["counts"]["lineage"] >= 1

def test_bridge_does_not_invent_destination_links():
    class C:
        def execute(self,q,params):
            rows=[{"payload_json":__import__('json').dumps(x)} for x in seed().get(params[0],[])]
            class R:
                def fetchall(self): return rows
            return R()
        def close(self): pass
    b=DataCoreBridge(lambda:C())
    result=b.enrich_journey({"places":[{"name":"Một điểm chưa có trong kho"}]})
    assert result["data_core"]["linked"] is False
    assert all(v==0 for v in result["data_core"]["counts"].values())
