from conversation_engine import ConversationIntelligenceEngine
from coverage_registry import CATEGORIES, resolve_known_place


def test_registry_recognizes_all_34_province_records_and_tourism_hubs():
    from province_data import PROVINCES_2025
    for p in PROVINCES_2025:
        assert resolve_known_place(p['name'])
        for hub in p.get('tourism_hubs', []):
            assert resolve_known_place(hub), (p['name'], hub)


def test_tourism_category_queries_do_not_silently_fail_for_recognized_places():
    e=ConversationIntelligenceEngine()
    places=['Bản Giốc','Pác Bó','Mộc Châu','Y Tý','Cát Bà','Đền Hùng','Tràng An',
            'Đại Nội','Ngũ Hành Sơn','Lý Sơn','Kỳ Co','Nha Trang','Đà Lạt',
            'Núi Bà Đen','Cái Răng','Mũi Cà Mau']
    for place in places:
        for category in CATEGORIES:
            r=e.answer(f"{place} {category} có gì cần biết cho HDV?")
            assert r['ok'] is True
            assert r['answer'].strip()
            assert r['places'], (place, category)


def test_unknown_fact_is_not_hallucinated():
    e=ConversationIntelligenceEngine()
    r=e.answer('Bản Giốc kể cho tôi một sự kiện lịch sử năm 1492 ở địa điểm này')
    assert r['ok'] is True
    assert 'chưa có đủ tri thức' in r['answer'] or 'chưa có đủ' in r['answer']
