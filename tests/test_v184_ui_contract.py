from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v184_home_removes_old_hero_copy():
    home=(ROOT/'templates/home.html').read_text(encoding='utf8')
    assert 'TRỢ LÝ AI CHUYÊN BIỆT CHO HƯỚNG DẪN VIÊN VIỆT NAM' not in home
    assert 'Trí tuệ đồng hành' not in home


def test_v184_uses_vietnamese_journey_label():
    base=(ROOT/'templates/base.html').read_text(encoding='utf8')
    assistant=(ROOT/'templates/ai_assistant.html').read_text(encoding='utf8')
    assert 'Trợ lý hành trình' in base
    assert 'Trợ lý hành trình' in assistant
