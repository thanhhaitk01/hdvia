# HDVIA V1.5 Beta - Vercel fixed package

## Fixes included
- `Authlib==1.6.5` is included in `requirements.txt` so the OAuth import works on Vercel.
- OAuth uses the existing root `oauth.py`; no broken `auth/oauth.py` import path is used.
- SQLite database and uploaded guide-card files use `/tmp/hdvia` because Vercel's deployment filesystem is read-only.
- Google, Facebook and Zalo OAuth routes remain `/auth/<provider>` and callbacks `/auth/<provider>/callback`.
- Manual public registration remains closed in Beta; users can sign in via configured social providers.

## Required Vercel Environment Variables
- `HDVIA_SECRET_KEY`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `FACEBOOK_CLIENT_ID`
- `FACEBOOK_CLIENT_SECRET`
- `ZALO_CLIENT_ID`
- `ZALO_CLIENT_SECRET`
- Optional: `HDVIA_PUBLIC_BASE_URL` (recommended as `https://www.hdvia.vn`)
- Optional: `HDVIA_COOKIE_SECURE=1`

## Deploy
Upload/overwrite the files at repository root, commit to `main`, then redeploy on Vercel.

## Important
Vercel `/tmp` storage is temporary. This package is suitable for the current Beta test, but persistent user/database storage should be moved to a managed database/storage service before production.
