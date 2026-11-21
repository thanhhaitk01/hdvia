# HDVIA Google Login Patch

This patch places the Google quick-login button directly below the normal HDVIA login button.

## Files

- `auth/oauth.py` - Authlib Google OAuth registration and callback.
- `templates/oauth_buttons.html` - Google/Facebook quick-login UI.
- `static/oauth-buttons.css` - button styling.
- `.env.example` - environment variable names.

## Required Vercel environment variables

Set these in Vercel:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

The Google Client ID is already filled in `.env.example`.

## Google OAuth redirect URI

Because the callback URL is generated with Flask `url_for(..., _external=True)`, the deployment's canonical HTTPS host is used. Register the resulting callback URL in Google Cloud Console:

`/auth/google/callback`

For example, if the canonical site is `https://hdvia.vn`, the URI is:

`https://hdvia.vn/auth/google/callback`

Do not commit `GOOGLE_CLIENT_SECRET` to GitHub.

## Important integration point

The application must call `register_oauth(app)` during Flask app initialization. If HDVIA already initializes/registers the OAuth blueprint elsewhere, merge the functions instead of registering the blueprint twice.
