from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_journey_has_single_content_block():
    text = (ROOT / "templates" / "journey.html").read_text()
    assert text.count("{% block content %}") == 1


def test_journey_post_form_has_csrf_token():
    text = (ROOT / "templates" / "journey.html").read_text()
    assert 'name="csrf_token"' in text


def test_journey_csrf_failure_has_recovery_template():
    text = (ROOT / "app.py").read_text()
    assert 'render_template("journey_csrf_error.html"' in text
    assert (ROOT / "templates" / "journey_csrf_error.html").exists()
