from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_curated_representative_image_registry_is_complete():
    from media_defaults import REPRESENTATIVE_MEDIA, media_for_slug
    expected = {"ha-noi", "ha-long", "hue", "da-nang", "hoi-an", "my-son", "nha-trang", "da-lat"}
    assert expected.issubset(REPRESENTATIVE_MEDIA)
    for slug in expected:
        media = media_for_slug(slug)
        assert media["image_url"].startswith("https://commons.wikimedia.org/wiki/Special:Redirect/file/")
        assert media["source_url"].startswith("https://commons.wikimedia.org/wiki/File:")
        assert media["license"]
        assert media["artist"]


def test_destination_context_code_surfaces_curated_image_metadata():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert '"image_url":media_for_slug(d["slug"]).get("image_url")' in app
    assert '"image_source_url":media_for_slug(d["slug"]).get("source_url")' in app
    assert '"image_license":media_for_slug(d["slug"]).get("license")' in app
    assert '"image_artist":media_for_slug(d["slug"]).get("artist")' in app


def test_journey_template_prefers_curated_image_then_live_fallback():
    html = (ROOT / "templates" / "journey.html").read_text(encoding="utf-8")
    assert "data-image-url" in html
    assert "if(node.dataset.imageUrl)" in html
    assert "fetchLive()" in html
    assert "node.dataset.liveFallbackTried" in html
