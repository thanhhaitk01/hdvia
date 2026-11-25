from knowledge_intelligence import destination_card, normalize_candidate, dedupe_candidates, validate_candidate


def test_destination_card_has_four_layers_and_confidence():
    card=destination_card("Đà Nẵng")
    assert set(card["layers"]) == {"geography","culture_history","tourism","nature_operations"}
    assert card["layer_counts"]["culture_history"] >= 1
    assert card["confidence"] in ("LOW","MEDIUM","HIGH")


def test_acquisition_normalize_dedupe_validate():
    a=normalize_candidate({"title":"Đà Nẵng","content":"Một nội dung đủ dài để kiểm thử candidate và nguồn dữ liệu bên ngoài.","destination":"Đà Nẵng"},"https://example.org/a","external")
    b=normalize_candidate({"title":"Đà Nẵng","content":"Một nội dung đủ dài để kiểm thử candidate và nguồn dữ liệu bên ngoài.","destination":"Đà Nẵng"},"https://example.org/b","external")
    assert len(dedupe_candidates([a,b])) == 1
    v=validate_candidate(a)
    assert v["status"] == "VALIDATED"
    assert v["confidence"] == "LOW"
