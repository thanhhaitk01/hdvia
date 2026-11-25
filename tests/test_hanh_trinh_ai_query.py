from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def test_unified_hanh_trinh_ai_ui():
    html=(ROOT/"templates/journey.html").read_text(encoding="utf-8")
    assert "HÀNH TRÌNH AI" in html
    assert 'name="query"' in html
    assert "Đà Nẵng mùa này có mưa không?" in html

def test_unified_nav_label():
    html=(ROOT/"templates/base.html").read_text(encoding="utf-8")
    assert "Hành Trình AI" in html
    assert "Lập & phân tích hành trình" not in html


def test_hanh_trinh_ai_has_predicted_question_surface():
    html=(ROOT/"templates/journey.html").read_text(encoding="utf-8")
    assert "CÂU HỎI GỢI Ý" in html
    assert "predicted_questions" in html
    assert "Độ tin cậy" in html
