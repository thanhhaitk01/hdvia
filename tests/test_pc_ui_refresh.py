from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pc_refresh_uses_adaptive_desktop_result_surface():
    html = (ROOT / 'templates' / 'journey.html').read_text(encoding='utf-8')
    css = (ROOT / 'static' / 'style.css').read_text(encoding='utf-8')
    assert 'journey-desktop-result' in html
    assert 'journey-mobile-legacy' in html
    assert 'result.get(\'days\')|length > 1' in html
    assert 'result.get(\'destination_context\')' in html
    assert 'ai-query-hints{display:none !important}' in css


def test_pc_refresh_does_not_change_mobile_legacy_surface():
    html = (ROOT / 'templates' / 'journey.html').read_text(encoding='utf-8')
    css = (ROOT / 'static' / 'style.css').read_text(encoding='utf-8')
    assert 'journey-mobile-legacy' in html
    assert '@media (max-width:900px)' in css
    assert '.journey-desktop-result{display:none !important}' in css
    assert '.journey-mobile-legacy{display:block}' in css


def test_pc_refresh_hides_the_two_requested_desktop_sections():
    css = (ROOT / 'static' / 'style.css').read_text(encoding='utf-8')
    assert '@media (min-width: 901px)' in css
    assert '.ai-query-hints{display:none !important}' in css
    assert '.journey-mobile-legacy{display:none !important}' in css
