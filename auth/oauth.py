import os
from flask import Blueprint, redirect, url_for, session, jsonify, render_template
from authlib.integrations.flask_client import OAuth

oauth_bp = Blueprint("oauth", __name__, url_prefix="/auth")
oauth = OAuth()

def init_oauth(app):
    oauth.init_app(app)

    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    if google_client_id and google_client_secret:
        oauth.register(
            name="google",
            client_id=google_client_id,
            client_secret=google_client_secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )

    facebook_app_id = os.getenv("FACEBOOK_APP_ID")
    facebook_app_secret = os.getenv("FACEBOOK_APP_SECRET")
    if facebook_app_id and facebook_app_secret:
        oauth.register(
            name="facebook",
            client_id=facebook_app_id,
            client_secret=facebook_app_secret,
            authorize_url="https://www.facebook.com/v24.0/dialog/oauth",
            access_token_url="https://graph.facebook.com/v24.0/oauth/access_token",
            api_base_url="https://graph.facebook.com/v24.0/",
            client_kwargs={"scope": "email,public_profile"},
        )

def _provider_enabled(name):
    return name in oauth._clients

@oauth_bp.get("/login/<provider>")
def login(provider):
    if not _provider_enabled(provider):
        return jsonify({
            "ok": False,
            "error": f"{provider} OAuth is not configured yet."
        }), 503

    client = oauth.create_client(provider)
    redirect_uri = url_for("oauth.callback", provider=provider, _external=True)
    return client.authorize_redirect(redirect_uri)

@oauth_bp.get("/callback/<provider>")
def callback(provider):
    if not _provider_enabled(provider):
        return jsonify({
            "ok": False,
            "error": f"{provider} OAuth is not configured yet."
        }), 503

    client = oauth.create_client(provider)
    token = client.authorize_access_token()

    if provider == "google":
        userinfo = token.get("userinfo")
        if not userinfo:
            userinfo = client.get("https://openidconnect.googleapis.com/v1/userinfo").json()
        user = {
            "provider": "google",
            "provider_id": userinfo.get("sub"),
            "name": userinfo.get("name"),
            "email": userinfo.get("email"),
            "avatar": userinfo.get("picture"),
        }
    else:
        profile = client.get("me?fields=id,name,email,picture").json()
        user = {
            "provider": "facebook",
            "provider_id": profile.get("id"),
            "name": profile.get("name"),
            "email": profile.get("email"),
            "avatar": ((profile.get("picture") or {}).get("data") or {}).get("url"),
        }

    # Temporary session bridge.
    # Replace/extend this with HDVIA's real user database + verified-user rules.
    # OPEN BETA: mọi tài khoản OAuth hợp lệ đều được phép vào hệ thống.
    # Không kiểm tra giấy phép HDV ở giai đoạn này.
    user["access_mode"] = os.getenv("HDVIA_AUTH_MODE", "open_beta")
    user["verified_guide_required"] = False
    session["hdvia_user"] = user
    return redirect(url_for("oauth.success"))

@oauth_bp.get("/success")
def success():
    user = session.get("hdvia_user")
    if not user:
        return redirect("/")
    return render_template("oauth_success.html", user=user)
