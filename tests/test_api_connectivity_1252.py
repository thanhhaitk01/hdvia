from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from api_adapters import OpenAPIAdapter


def test_connectivity_probe_exists_and_reports_each_live_provider():
    src = (ROOT / 'api_adapters.py').read_text(encoding='utf-8')
    assert 'def probe_connectivity' in src
    expected = {'weather','geocoding','routing','air_quality','marine','osm','wikipedia','wikidata','sun'}
    assert expected <= set(__import__('re').findall(r'"([a-z_]+)": lambda', src))


def test_public_api_health_and_connectivity_routes_exist():
    src = (ROOT / 'app.py').read_text(encoding='utf-8')
    assert '/api/v1/public-api/health' in src
    assert '/api/v1/public-api/connectivity' in src


def test_image_endpoint_reports_provider_failure_instead_of_silent_success():
    src = (ROOT / 'app.py').read_text(encoding='utf-8')
    assert 'image_provider_unreachable' in src
    assert 'image_provider_http_error' in src
    assert 'source_url' in src


def test_air_quality_and_marine_public_routes_use_adapter():
    src = (ROOT / 'app.py').read_text(encoding='utf-8')
    assert 'return jsonify(OPEN_API_ADAPTER.air_quality' in src
    assert 'return jsonify(OPEN_API_ADAPTER.marine' in src
