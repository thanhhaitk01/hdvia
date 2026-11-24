from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from unified_destination_search import unified_search

def test_hanh_trinh_ai_module_replaces_destination_nav():
    html=(ROOT/'templates/base.html').read_text(encoding='utf8')
    assert 'Hành trình AI' in html
    assert 'Điểm đến & thông tin' not in html

def test_unified_search_recognizes_hanoi_and_returns_destination_context():
    r=unified_search('Hà Nội')
    assert r['intent']=='PLACE'
    assert r['context']['provinces']
    assert any(d['name']=='Hà Nội' for d in r['context']['destinations'])

def test_unified_search_recognizes_landmark_as_related_place():
    r=unified_search('Lăng Khải Định')
    assert r['intent']=='PLACE'
    assert r['context']['primary_destination']['name']=='Huế'
    assert any('Lăng Khải Định' in h for h in r['context']['primary_destination'].get('highlights',[]))

def test_unified_search_recognizes_itinerary():
    r=unified_search('Đà Nẵng → Hội An → Huế 4 ngày')
    assert r['intent']=='ITINERARY'


def test_hanh_trinh_ai_is_single_input_module():
    html=(ROOT/'templates/journey.html').read_text(encoding='utf8')
    assert 'Một giao diện duy nhất' in html
    assert 'name="query"' in html
    assert 'name="itinerary"' not in html
    assert 'NHẬP HÀNH TRÌNH' not in html

def test_hanh_trinh_ai_supports_both_intents_in_same_input():
    assert unified_search('Hà Nội')['intent']=='PLACE'
    assert unified_search('Đà Nẵng → Hội An → Huế 4 ngày')['intent']=='ITINERARY'
