from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v185_location_context_endpoint_exists():
    app=(ROOT/'app.py').read_text(encoding='utf8')
    assert '/api/v1/location-context' in app
    assert 'nearest_destination' in app

def test_v185_home_has_location_aware_shell():
    home=(ROOT/'templates/home.html').read_text(encoding='utf8')
    base=(ROOT/'templates/base.html').read_text(encoding='utf8')
    css=(ROOT/'static/style.css').read_text(encoding='utf8')
    assert 'location-hero' in home
    assert 'data-location-label' in home
    assert 'location-background-ready' in css
    assert 'api/v1/location-context' in base


def test_v185_navigation_is_consolidated():
    base=(ROOT/'templates/base.html').read_text(encoding='utf8')
    home=(ROOT/'templates/home.html').read_text(encoding='utf8')
    journey=(ROOT/'templates/journey.html').read_text(encoding='utf8')
    assert '/tro-ly-ai' not in base
    assert 'Thời tiết & Cảnh báo' not in base
    assert all(label in home for label in ['Lập & phân tích hành trình','Điểm đến & thông tin','Kho kinh nghiệm HDV','Tài khoản & xác minh'])
    assert 'journey-layout' in journey and '<aside class="side">' not in journey
