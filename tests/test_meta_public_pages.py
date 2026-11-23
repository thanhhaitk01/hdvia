from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]

def test_meta_public_policy_pages_contract():
    src = (ROOT / "app.py").read_text(encoding="utf8")
    ast.parse(src)
    for route in ("/dieu-khoan", "/chinh-sach", "/xoa-du-lieu"):
        assert route in src
    assert (ROOT / "templates" / "privacy.html").exists()
    assert (ROOT / "templates" / "terms.html").exists()
    assert (ROOT / "templates" / "data_deletion.html").exists()

def test_data_deletion_page_has_contact_and_instructions():
    src = (ROOT / "templates" / "data_deletion.html").read_text(encoding="utf8")
    assert "thanhhaitk01@gmail.com" in src
    assert "Yêu cầu xoá dữ liệu HDVIA" in src
    assert "Facebook" in src and "Google" in src and "Zalo" in src
