from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v18_branding_and_vietnamese_ui():
    base=(ROOT/'templates/base.html').read_text(encoding='utf8')
    home=(ROOT/'templates/home.html').read_text(encoding='utf8')
    assert 'Trí tuệ đồng hành, hành trình chủ động.' in base
    assert 'hdvia-logo.png' in base
    for phrase in ['Phân tích hành trình','Thời tiết hành trình','Cảnh báo rủi ro','Lộ trình & khoảng cách','Trợ lý thuyết minh','Phương án dự phòng','Thông tin điểm đến','Kho kinh nghiệm']:
        assert phrase in home or phrase in base

def test_knowledge_pages_exist():
    for name in ['knowledge.html','knowledge_write.html','knowledge_detail.html']:
        assert (ROOT/'templates'/name).exists()
    assert (ROOT/'static/assets/hdvia-logo.png').exists()
