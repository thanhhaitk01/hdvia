from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_destinations_template_renders_representative_image_url():
    html=(ROOT / "templates" / "destinations.html").read_text(encoding="utf-8")
    assert "destination-representative-image" in html
    assert "d.get('image_url')" in html
    assert 'alt="Ảnh đại diện {{d.name}}"' in html

def test_destination_detail_template_renders_representative_image_url():
    html=(ROOT / "templates" / "destination_detail.html").read_text(encoding="utf-8")
    assert "destination-detail-image" in html
    assert "destination.get('image_url')" in html
    assert 'alt="Ảnh đại diện {{destination.name}}"' in html

def test_rendering_is_backed_by_destination_context_metadata():
    app=(ROOT / "app.py").read_text(encoding="utf-8")
    assert '"image_url":media_for_slug(d["slug"]).get("image_url")' in app
    assert '"image_source_url":media_for_slug(d["slug"]).get("source_url")' in app
