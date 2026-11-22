# HDVIA Beta 1.6 — Vercel Zero-Config Flask Fix

## Deployment change

This build removes the legacy `builds` + catch-all `routes` configuration from `vercel.json`.
The application keeps the root `app.py` entrypoint and the top-level Flask `app` object.

Vercel's current Flask runtime detects Flask applications from `requirements.txt` and supported
entrypoints such as `app.py`, so the legacy routing layer is unnecessary and can interfere with
framework-defined deployment behavior.

## Important runtime note

This package was regression-tested in the available environment. The environment does not have
Flask/Authlib installed, so a real Vercel cold-start cannot be claimed from local execution alone.
After deployment, the authoritative check is the Vercel Runtime/Function log and the production URL.
