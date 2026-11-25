from knowledge_expansion import KnowledgeExpansionEngine, coverage, knowledge_gaps, graph_for_destination
from knowledge_intelligence import destination_card

def test_expansion_returns_coverage_gaps_graph():
    x=KnowledgeExpansionEngine().inspect("Đà Nẵng")
    assert x["coverage"]["destination"] == "Đà Nẵng"
    assert isinstance(x["gaps"], list)
    assert x["graph"]["node_count"] >= 1

def test_profile_is_non_destructive():
    base=destination_card("Đà Nẵng")
    india=destination_card("Đà Nẵng", tourist_profile="india")
    assert base["name"] == india["name"] == "Đà Nẵng"
    assert india["tourist_profile"] == "india"
    assert "knowledge_expansion" in india

def test_guide_contribution_is_candidate_only():
    c=KnowledgeExpansionEngine().contribution(destination="Hội An",title="Góc nhìn HDV",content="Một kinh nghiệm thực địa đủ dài để vượt kiểm tra tối thiểu.")
    assert c["status"] == "CANDIDATE"
    assert c["provenance_required"] is True

def test_graph_is_deterministic_shape():
    a=graph_for_destination("Huế"); b=graph_for_destination("Huế")
    assert a["node_count"] == b["node_count"]
    assert a["edge_count"] == b["edge_count"]
