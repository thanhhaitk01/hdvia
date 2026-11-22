import os
from authlib.integrations.flask_client import OAuth

oauth = OAuth()

def init_oauth(app):
    oauth.init_app(app)
    if os.getenv('GOOGLE_CLIENT_ID') and os.getenv('GOOGLE_CLIENT_SECRET'):
        oauth.register(
            name='google',
            client_id=os.getenv('GOOGLE_CLIENT_ID'),
            client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={'scope': 'openid email profile'},
        )
    if os.getenv('FACEBOOK_CLIENT_ID') and os.getenv('FACEBOOK_CLIENT_SECRET'):
        oauth.register(
            name='facebook',
            client_id=os.getenv('FACEBOOK_CLIENT_ID'),
            client_secret=os.getenv('FACEBOOK_CLIENT_SECRET'),
            access_token_url='https://graph.facebook.com/oauth/access_token',
            authorize_url='https://www.facebook.com/dialog/oauth',
            api_base_url='https://graph.facebook.com/',
            client_kwargs={'scope': 'public_profile,email'},
        )
    if os.getenv('ZALO_CLIENT_ID') and os.getenv('ZALO_CLIENT_SECRET'):
        oauth.register(
            name='zalo',
            client_id=os.getenv('ZALO_CLIENT_ID'),
            client_secret=os.getenv('ZALO_CLIENT_SECRET'),
            access_token_url='https://oauth.zaloapp.com/v4/access_token',
            authorize_url='https://oauth.zaloapp.com/v4/permission',
            api_base_url='https://graph.zalo.me/v2.0/',
            client_kwargs={'scope': 'id_name'},
        )
    return oauth

def provider_enabled(name):
    return bool(oauth.create_client(name))
