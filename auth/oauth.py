import os
from flask import Blueprint, redirect, url_for, session, abort
from authlib.integrations.flask_client import OAuth

oauth = OAuth()

oauth_bp = Blueprint("oauth", __name__, url_prefix="/auth")


def init_oauth(app):
    """Initialize Google OAuth for HDVIA."""
    oauth.init_app(app)

    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if not google_client_id or not google_client_secret:
        app.logger.warning(
            "Google OAuth is disabled: GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET "
            "are not configured."
        )
        return

    oauth.register(
        name="google",
        client_id=google_client_id,
        client_secret=google_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


@oauth_bp.get("/google/login")
def google_login():
    if not os.getenv("GOOGLE_CLIENT_ID") or not os.getenv("GOOGLE_CLIENT_SECRET"):
        abort(503, description="Google OAuth is not configured.")

    redirect_uri = url_for("oauth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@oauth_bp.get("/google/callback")
def google_callback():
    if not os.getenv("GOOGLE_CLIENT_ID") or not os.getenv("GOOGLE_CLIENT_SECRET"):
        abort(503, description="Google OAuth is not configured.")

    token = oauth.google.authorize_access_token()
    userinfo = token.get("userinfo")

    if not userinfo:
        userinfo = oauth.google.userinfo(token=token)

    # Keep the Google identity in the session for the existing HDVIA
    # authentication/user layer to consume.
    session["google_user"] = {
        "sub": userinfo.get("sub"),
        "email": userinfo.get("email"),
        "name": userinfo.get("name"),
        "picture": userinfo.get("picture"),
    }

    # Existing HDVIA login/session handling can be added here if the
    # application already has a user model.
    return redirect(url_for("home"))


def register_oauth(app):
    init_oauth(app)
    app.register_blueprint(oauth_bp)
