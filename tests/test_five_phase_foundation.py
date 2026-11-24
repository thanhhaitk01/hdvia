from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
APP=(BASE/'app.py').read_text(encoding='utf-8')

def test_phase_modules_present():
    for name in ('copilot_engine','external_connect','agent_engine','OPEN_API_CATALOG','learning_pipeline'):
        assert name in APP

def test_open_api_routes_present():
    for route in ('/api/v1/openapi/status','/api/v1/openapi/copilot','/api/v1/openapi/agent/inspect-tour','/api/v1/openapi/connect/status'):
        assert route in APP

def test_mobile_contract_exists():
    assert (BASE/'mobile/README.md').exists()

def test_controlled_learning():
    text=(BASE/'knowledge_learning.py').read_text(encoding='utf-8')
    assert 'CANDIDATE' in text and 'provenance_required_for_publish' in text
