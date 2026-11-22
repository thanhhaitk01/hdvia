from knowledge_layer import search_knowledge, answer_from_knowledge


def test_knowledge_base_has_central_vietnam_seed_data():
    hits = search_knowledge("Huế lịch sử cố đô")
    assert hits
    assert any("Huế" in x["destination"] for x in hits)


def test_knowledge_answer_is_retrieval_not_empty():
    answer, hits = answer_from_knowledge("Hội An ẩm thực")
    assert hits
    assert "Kho tri thức" in answer
