from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_destination_page_hides_province_grid_until_search():
    html=(ROOT/'templates/destinations.html').read_text(encoding='utf8')
    assert 'id="searchResults" hidden' in html
    assert 'id="emptySearch"' in html
    assert 'const PROVINCES=' in html
    assert 'filterDest()' in html
    assert 'province-grid' in html
    assert '34 TỈNH' not in html

def test_destination_page_supports_province_and_destination_search():
    html=(ROOT/'templates/destinations.html').read_text(encoding='utf8')
    assert 'PROVINCES.filter' in html
    assert 'DESTINATIONS.filter' in html
    assert 'p.tourism_hubs' in html
    assert 'd.overview' in html
    assert 'tojson' in html
