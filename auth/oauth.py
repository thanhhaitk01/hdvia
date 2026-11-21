import os
from flask import Blueprint, redirect, url_for, session, abort
from authlib.integrations.flask_client import OAuth

oauth = OAuth()
oauth_bp = Blueprint("oauth", __name__, url_prefix="/auth")


def init_oauth(app):
    oauth.init_app(app)

    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    facebook_client_id = os.getenv("FACEBOOK_CLIENT_ID")
    facebook_client_secret = os.getenv("FACEBOOK_CLIENT_SECRET")

    if google_client_id and google_client_secret:
        oauth.register(
            name="google",
            client_id=google_client_id,
            client_secret=google_client_secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )

    if facebook_client_id and facebook_client_secret:
        oauth.register(
            name="facebook",
            client_id=facebook_client_id,
            client_secret=facebook_client_secret,
            authorize_url="https://www.facebook.com/v23.0/dialog/oauth",
            access_token_url="https://graph.facebook.com/v23.0/oauth/access_token",
            api_base_url="https://graph.facebook.com/v23.0/",
            client_kwargs={"scope": "email,public_profile"},
        )

    app.register_blueprint(oauth_bp)


@oauth_bp.route("/login/<provider>")
def oauth_login(provider):
    if provider not in ("google", "facebook"):
        abort(404)

    client = oauth.create_client(provider)
    if client is None:
        abort(503, description=f"OAuth provider '{provider}' chưa được cấu hình.")

    redirect_uri = url_for("oauth.oauth_callback", provider=provider, _external=True)
    return client.authorize_redirect(redirect_uri)


@oauth_bp.route("/callback/<provider>")
def oauth_callback(provider):
    if provider not in ("google", "facebook"):
        abort(404)

    client = oauth.create_client(provider)
    if client is None:
        abort(503, description=f"OAuth provider '{provider}' chưa được cấu hình.")

    token = client.authorize_access_token()

    if provider == "google":
        userinfo = token.get("userinfo") or client.userinfo()
        profile = {
            "provider": "google",
            "provider_id": userinfo.get("sub"),
            "email": userinfo.get("email"),
            "name": userinfo.get("name"),
            "picture": userinfo.get("picture"),
        }
    else:
        resp = client.get("me", params={"fields": "id,name,email,picture.type(large)"})
        data = resp.json()
        picture = data.get("picture", {}).get("data", {}).get("url")
        profile = {
            "provider": "facebook",
            "provider_id": data.get("id"),
            "email": data.get("email"),
            "name": data.get("name"),
            "picture": picture,
        }

    # Open-Beta: cho phép OAuth login mà chưa yêu cầu Verified Guide approval.
    # Giữ OAuth identity trong session để dùng cho bước đồng bộ tài khoản tiếp theo.
    session["oauth_user"] = profile
    session["authenticated"] = True
    return redirect(url_for("oauth.oauth_success"))


@oauth_bp.route("/success")
def oauth_success():
    if not session.get("authenticated"):
        return redirect(url_for("login"))
    return redirect(url_for("home"))
