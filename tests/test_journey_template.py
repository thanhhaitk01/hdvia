from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_journey_template_renders_vietnamese_result_sections():
    html=(ROOT/'templates/journey.html').read_text(encoding='utf-8')
    for phrase in ['result.places','Thời tiết hành trình','Cảnh báo','Trợ lý thuyết minh','Phương án dự phòng','Đánh giá kết quả','/api/v1/journey/feedback']:
        assert phrase in html

def test_journey_template_avoids_old_technical_labels():
    html=(ROOT/'templates/journey.html').read_text(encoding='utf-8')
    assert 'Tour Briefing cho HDV' not in html
    assert 'Plan B theo ngày' not in html
