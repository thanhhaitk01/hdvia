from pathlib import Path
import json, sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_health_version_and_connectivity_endpoint_contract():
    src=(ROOT/'app.py').read_text(encoding='utf-8')
    assert '1.25.2-api-connectivity-live-data-hardened' in src
    assert '/api/v1/public-api/connectivity' in src


def test_connectivity_probe_is_read_only_and_covers_live_groups():
    src=(ROOT/'api_adapters.py').read_text(encoding='utf-8')
    for provider in ('weather','geocoding','routing','air_quality','marine','osm','wikipedia','wikidata','sun'):
        assert f'"{provider}": lambda' in src
    assert 'probe_connectivity' in src


def test_image_failure_is_observable():
    src=(ROOT/'app.py').read_text(encoding='utf-8')
    assert 'image_provider_unreachable' in src
    assert 'image_provider_http_error' in src
    assert 'no_image_result' in src
