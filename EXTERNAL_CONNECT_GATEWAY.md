# HDVIA 1.10.14 — External Connect Gateway

HDVIA now has a provider-neutral gateway for permitted external data and AI services.

## Providers
- Google Places (API key)
- Google Custom Search JSON API (existing acquisition connector)
- YouTube Data API v3
- Meta Graph API / webhooks-ready contract
- OpenAI Responses API
- Google Gemini API
- Anthropic Messages API

Secrets are read only from server environment variables and are never returned by status endpoints or stored in warehouse records.

## Data policy
External responses are evidence/context. Curated knowledge must still pass the existing CANDIDATE → VALIDATED → REVIEW → PUBLISHED flow before becoming warehouse data.

## Runtime endpoints
- `GET /api/v1/external-gateway/status`
- `GET /api/v1/external-gateway/google-places?q=...`
- `GET /api/v1/external-gateway/youtube-search?q=...`
- `POST /api/v1/external-gateway/meta-graph`
- `POST /api/v1/external-gateway/ai`

Credentials required in deployment environment:
`GOOGLE_MAPS_API_KEY`, `YOUTUBE_API_KEY`, `META_ACCESS_TOKEN`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`.

Google CSE continues to use `GOOGLE_CSE_API_KEY` + `GOOGLE_CSE_CX` through the acquisition layer.
