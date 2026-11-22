# HDVIA V1.4 Deployment

## Local
python -m venv .venv

Windows:
.venv\\Scripts\\activate

macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python app.py

Open http://127.0.0.1:8000

## Docker
docker compose up --build

## Environment
HDVIA_SECRET_KEY=<strong-production-secret>
HDVIA_DEMO_ADMIN_PASSWORD=<new-admin-password>
HDVIA_COOKIE_SECURE=1
PORT=8000

## Important
- SQLite is for MVP/testing.
- Production should use PostgreSQL/MySQL.
- HTTPS is required before public launch.
- Guide-card images should move to private object storage.
- Add real OTP/MFA, rate limiting, CSRF, WAF, monitoring and backup/recovery.
- Weather and image providers are external services; configure/replace providers according to production policy.
