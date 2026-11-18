# HDVIA V1.6 Beta — Identity / Verified Guide / Admin

## Normal user
- Phone + OTP: `/login`
- Google/Zalo/Facebook: OAuth integration points are `/auth/google`, `/auth/zalo`, `/auth/facebook`.
- Normal users are automatically created with role `USER`.
- No Guide card verification is required for normal features.

## Verified Guide
- Existing user opens `/guide/apply`.
- Submit Guide card and information.
- Admin reviews the application.
- APPROVE changes the same user from `USER` to `GUIDE` and trust level `L2`.

## Admin
Admin login is deliberately separate from normal-user authentication:

- URL: `/admin/login`
- Dashboard: `/admin`
- Guide verification: `/admin/guides`
- Audit: `/admin/audit`

Environment variables:
- `HDVIA_ADMIN_EMAIL`
- `HDVIA_ADMIN_PASSWORD`
- `HDVIA_SECRET_KEY`
- `HDVIA_COOKIE_SECURE=1` in production
- `HDVIA_OTP_DEMO_MODE=1` only for local testing

The Admin account must not be created through phone OTP, Google, Zalo or Facebook.
