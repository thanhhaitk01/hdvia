from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'templates/journey.html').read_text(encoding='utf-8')
CSS=(ROOT/'static/style.css').read_text(encoding='utf-8')

def test_integrated_journey_timeline_surface():
    assert 'THÔNG TIN TÍCH HỢP TRONG HÀNH TRÌNH' in HTML
    assert 'journey-timeline' in HTML
    assert 'journey-place-intel' in HTML
    assert 'Điểm nổi bật' in HTML
    assert 'Văn hóa' in HTML
    assert 'Lịch sử' in HTML
    assert 'Ẩm thực' in HTML
    assert 'Kinh nghiệm HDV' in HTML
    assert 'Dữ liệu rủi ro liên kết' in HTML

def test_integrated_journey_styles_exist():
    for token in ('journey-overview-card','journey-summary-metrics','journey-timeline','journey-day-intel','journey-fact-grid'):
        assert token in CSS
