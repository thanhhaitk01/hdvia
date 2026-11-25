from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v18_branding_and_vietnamese_ui():
    base=(ROOT/'templates/base.html').read_text(encoding='utf8')
    home=(ROOT/'templates/home.html').read_text(encoding='utf8')
    assert 'Bạn Đồng Hành Du Lịch Việt Nam' in base
    assert 'hdvia-logo.png' in base
    assert 'Hành Trình AI' in base
    assert 'Điểm đến & thông tin' not in home
    assert 'Kho kinh nghiệm HDV' in home
    assert 'Thời tiết' in home
    assert 'Cảnh báo' in home

def test_knowledge_pages_exist():
    for name in ['knowledge.html','knowledge_write.html','knowledge_detail.html']:
        assert (ROOT/'templates'/name).exists()
    assert (ROOT/'static/assets/hdvia-logo.png').exists()
