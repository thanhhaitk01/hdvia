# HDVIA Beta 1.8.3 — OAuth Dual-Domain Fix

## Scope
- Supports OAuth callback URLs on both `hdvia.vn` and `www.hdvia.vn`.
- Applies to Google, Facebook, and Zalo routes already present in HDVIA.
- Uses the hostname that started the OAuth flow so the session/state cookie remains on the same origin.
- Trusts Vercel forwarded host/protocol headers through `ProxyFix`.

## Required provider configuration
Register both exact callback URLs for each provider:

### Google
- `https://hdvia.vn/auth/google/callback`
- `https://www.hdvia.vn/auth/google/callback`

### Facebook
- `https://hdvia.vn/auth/facebook/callback`
- `https://www.hdvia.vn/auth/facebook/callback`

### Zalo
- `https://hdvia.vn/auth/zalo/callback`
- `https://www.hdvia.vn/auth/zalo/callback`

## Vercel environment variables
Set `HDVIA_ALLOWED_HOSTS=hdvia.vn,www.hdvia.vn` in Production.
Keep the existing provider client IDs/secrets in Vercel Environment Variables.
Redeploy after changing environment variables.
