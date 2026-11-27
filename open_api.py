"""Versioned Open API helpers. API keys are hashed and never returned."""
from __future__ import annotations
import hashlib, secrets
from datetime import datetime, timezone

def hash_key(raw): return hashlib.sha256(raw.encode()).hexdigest()
def issue_key(prefix="hdvia"):
    raw=f"{prefix}_{secrets.token_urlsafe(32)}"; return raw,hash_key(raw)
def utcnow(): return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

OPEN_API_VERSION="v1"
OPEN_API_CATALOG={
    "/api/v1/openapi/status":"GET",
    "/api/v1/openapi/journey/analyze":"POST",
    "/api/v1/openapi/copilot":"POST",
    "/api/v1/openapi/agent/inspect-tour":"POST",
    "/api/v1/openapi/connect/status":"GET",
    "/api/v1/public-api/health":"GET",
    "/api/v1/public-api/connectivity":"GET",
    "/api/v1/public-api/catalog":"GET",
    "/api/v1/public-api/weather":"GET",
    "/api/v1/public-api/geocode":"GET",
    "/api/v1/public-api/route":"GET",
    "/api/v1/public-api/sun":"GET",
    "/api/v1/public-api/osm":"GET",
    "/api/v1/public-api/destination/enrich":"GET",
    "/api/v1/public-api/opentripmap/places":"GET",
    "/api/v1/public-api/opentripmap/details":"GET",
}
