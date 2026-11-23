"""HDVIA Connect HTTP helpers for external-platform integration."""
from flask import Blueprint, jsonify
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
