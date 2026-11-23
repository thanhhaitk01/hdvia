"""HDVIA Connect HTTP helpers for external-platform integration."""
from flask import Blueprint, jsonify, render_template
from connect_core import build_registry

CONNECT_VERSION = "1.9.0-beta-connect-foundation"
connect_bp = Blueprint("connect", __name__, url_prefix="/api/v1/connect")


def init_connect_blueprint(app, provider_enabled):
    """Attach the provider-neutral registry once during app startup."""
    if "hdvia_connect_registry" in app.extensions:
        return app.extensions["hdvia_connect_registry"]
    registry = build_registry(provider_enabled)
    app.extensions["hdvia_connect_registry"] = registry
    app.register_blueprint(connect_bp)
    return registry


@connect_bp.get("/status")
def connect_status():
    from flask import current_app
    registry = current_app.extensions["hdvia_connect_registry"]
    return jsonify({
        "ok": True,
        "version": CONNECT_VERSION,
        "connectors": registry.public_status(),
    })


@connect_bp.get("/health")
def connect_health():
    """Compact health view for the Connect foundation."""
    from flask import current_app
    registry = current_app.extensions["hdvia_connect_registry"]
    items = registry.public_status()
    return jsonify({
        "ok": True,
        "version": CONNECT_VERSION,
        "enabled": [x["name"] for x in items if x["enabled"]],
        "disabled": [x["name"] for x in items if not x["enabled"]],
        "connectors": items,
    })


@connect_bp.get("/dashboard")
def connect_dashboard():
    """Human-readable Connect status dashboard; no secrets or tokens are shown."""
    from flask import current_app
    registry = current_app.extensions["hdvia_connect_registry"]
    return render_template("connect_dashboard.html", connectors=registry.public_status(), version=CONNECT_VERSION)


@connect_bp.get("/<provider>/status")
def provider_status(provider):
    """Return safe status for one registered provider."""
    from flask import current_app
    registry = current_app.extensions["hdvia_connect_registry"]
    item = registry.get(provider)
    if item is None:
        return jsonify({"ok": False, "error": "Provider không tồn tại."}), 404
    return jsonify({
        "ok": True,
        "version": CONNECT_VERSION,
        "connector": {
            "name": item.name,
            "display_name": item.display_name,
            "category": item.category,
            "enabled": item.enabled,
        },
    })
