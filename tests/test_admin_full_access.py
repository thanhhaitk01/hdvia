from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
APP=(BASE/"app.py").read_text(encoding="utf-8")
BASE_HTML=(BASE/"templates/base.html").read_text(encoding="utf-8")

def test_admin_bootstrap_is_super_admin():
    assert '"SUPER_ADMIN","L4","ACTIVE"' in APP
    assert 'admin@hdvia.local' in APP
    assert 'Nhatkhang@123' in APP

def test_admin_has_full_permission_wildcard():
    assert '"ADMIN":{"*"}' in APP
    assert '"SUPER_ADMIN":{"*"}' in APP

def test_admin_management_routes_and_navigation():
    for route in ('/admin','/admin/users','/admin/guides','/admin/kho-du-lieu','/admin/kinh-nghiem','/admin/audit'):
        assert route in APP or route in BASE_HTML
    assert 'href="/admin"' in BASE_HTML
    assert 'href="/admin/users"' in BASE_HTML
