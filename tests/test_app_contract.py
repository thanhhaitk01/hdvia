from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[1]

def test_app_compiles_and_keeps_routes():
    src=(ROOT/'app.py').read_text(encoding='utf8'); ast.parse(src)
    for route in ['/','/journey','/api/v1/journey/analyze','/api/v1/weather','/api/v1/place-image','/api/v1/route','/health','/__version','/profile','/account/connections','/guide/apply','/admin/guides','/admin/audit','/kinh-nghiem','/kinh-nghiem/viet','/data-deletion','/data_deletion']:
        assert route in src

def test_feedback_and_knowledge_contracts_exist():
    src=(ROOT/'app.py').read_text(encoding='utf8')
    for x in ['/api/v1/journey/feedback','journey_feedback','knowledge_posts','knowledge.write','knowledge.read']:
        assert x in src

def test_beta_all_logged_in_user_permissions_include_core_features():
    src=(ROOT/'app.py').read_text(encoding='utf8')
    assert '"USER"' in src
    for p in ['journey.analyze','weather.read','destination.read','ai.assistant.use','ai.copilot.use','itinerary.optimize','knowledge.write']:
        assert p in src


def test_release_version_and_unified_destination_contract():
    root=Path(__file__).resolve().parents[1]
    assert (root/'VERSION').read_text(encoding='utf-8').strip() == '1.23.1-ai-connect-self-update'
    html=(root/'templates/base.html').read_text(encoding='utf-8')
    assert 'href="/journey"' in html
    assert 'Điểm đến & thông tin' not in html
