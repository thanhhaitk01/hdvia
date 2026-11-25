from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_journey_template_renders_vietnamese_result_sections():
    html=(ROOT/'templates/journey.html').read_text(encoding='utf-8')
    for phrase in ['result.places','Thời tiết hành trình','Cảnh báo','TRỢ LÝ THUYẾT MINH','Phương án dự phòng','Đánh giá kết quả','/api/v1/journey/feedback']:
        assert phrase in html

def test_journey_template_avoids_old_technical_labels():
    html=(ROOT/'templates/journey.html').read_text(encoding='utf-8')
    assert 'Tour Briefing cho HDV' not in html
    assert 'Plan B theo ngày' not in html

def test_journey_analysis_tabs_are_clickable_and_target_sections():
    html=(ROOT/'templates/journey.html').read_text(encoding='utf-8')
    for href in ['#tong-quan','#thoi-tiet','#canh-bao','#lo-trinh','#du-phong']:
        assert f'href="{href}"' in html
    for section_id in ['id="tong-quan"','id="thoi-tiet"','id="canh-bao"','id="lo-trinh"','id="du-phong"']:
        assert section_id in html
    assert '<span class="active">🗺 Tổng quan</span>' not in html

def test_journey_template_does_not_render_raw_result_json():
    html=(ROOT/'templates/journey.html').read_text(encoding='utf-8')
    assert 'tojson' not in html
    assert '{{result.weather}}' not in html
    assert '{{result.risk_map}}' not in html
    assert '{{result.risks}}' not in html
    assert "result.places|map(attribute='name')|join(' · ')" in html


def test_journey_template_unifies_destination_and_briefing_without_separate_module():
    html=(ROOT/'templates/journey.html').read_text(encoding='utf-8')
    assert 'id="diem-den"' in html
    assert 'TRỢ LÝ THUYẾT MINH' in html
    assert 'quality' in html
    assert 'destinations.html' not in html

def test_journey_has_six_analysis_sections():
    html=(ROOT/'templates/journey.html').read_text(encoding='utf-8')
    for href in ['#tong-quan','#diem-den','#thoi-tiet','#canh-bao','#lo-trinh','#du-phong']:
        assert f'href="{href}"' in html
