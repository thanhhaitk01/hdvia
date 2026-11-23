from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_unified_session_contract_is_present():
    src=(ROOT/'app.py').read_text(encoding='utf8')
    assert 'PERMANENT_SESSION_LIFETIME=timedelta(days=30)' in src
    assert 'SESSION_REFRESH_EACH_REQUEST=True' in src
    assert 'def establish_session(u):' in src
    assert 'session["user_snapshot"] = _user_snapshot(u)' in src
    assert 'def current_user():' in src
    assert 'snap=session.get("user_snapshot")' in src
    assert 'session.clear()' in src
