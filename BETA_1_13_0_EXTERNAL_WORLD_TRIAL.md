# HDVIA Beta 1.13.0 — External World Connectivity Trial

Bản chạy thử hoàn thiện 4 tầng trước khi bước sang AI Travel Agent cao cấp:

1. **Two-way data sync**: pull/push + dedup + trace id.
2. **Provider integration**: lifecycle `connect/read/write/disconnect` bằng HTTP provider thật, không còn contract-only placeholder.
3. **External AI/API orchestration**: provider order + retry + fallback.
4. **Agent execution**: permission gate, audit trace, dry-run mặc định; live execution chỉ khi bật `HDVIA_AGENT_LIVE_EXECUTION=1`.

## Cấu hình provider

Chỉ truyền credential ở runtime:
- `HDVIA_GOOGLE_API_BASE`, `HDVIA_GOOGLE_API_TOKEN`
- `HDVIA_FACEBOOK_API_BASE`, `HDVIA_FACEBOOK_API_TOKEN`
- `HDVIA_ZALO_API_BASE`, `HDVIA_ZALO_API_TOKEN`
- `HDVIA_MAPS_API_BASE`, `HDVIA_MAPS_API_TOKEN`
- `HDVIA_EXTERNAL_AI_BASE`, `HDVIA_EXTERNAL_AI_TOKEN`

Không lưu secret vào source/ZIP.

## API trial

- `GET /api/v1/external-world/status`
- `POST /api/v1/external-world/sync/pull`
- `POST /api/v1/external-world/sync/push`
- `POST /api/v1/external-world/ai/orchestrate`
- `POST /api/v1/external-world/agent/execute`

## Safety

- URL validation chống SSRF.
- Agent dry-run mặc định.
- Live execution cần bật bằng environment variable.
- Mọi execution có trace/audit record.
- Provider credentials không nằm trong source.
- `POST /api/v1/external-world/provider/<provider>/connect`
- `POST /api/v1/external-world/provider/<provider>/disconnect`
- `GET /api/v1/external-world/agent/audit`
