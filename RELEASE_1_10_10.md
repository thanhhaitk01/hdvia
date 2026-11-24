# HDVIA Beta 1.10.10 — Data Core + Acquisition Hardened

Baseline: Beta 1.10.9 Data Acquisition Ready.

## Included
- 8 linked data warehouses through Data Core.
- `Điểm đến & Thông tin` remains the user-facing knowledge/destination module.
- Controlled Data Acquisition pipeline: external source -> extraction -> CANDIDATE -> validation/review -> publication.
- Official Google Custom Search JSON API connector when configured; no Google HTML scraping.
- Source/lineage metadata for acquired records.
- Admin-only acquisition endpoints.
- SSRF hardening: private/local/link-local/reserved network targets are rejected by default and redirects are rejected.
- Existing legacy warehouse collections/routes remain compatible.

## Verification
- Full automated regression suite: 71 passed.
- Python bytecode compilation: passed before cleanup.
- Flask live import was not executed in this runner because Flask is not installed in the execution environment; deployment/runtime dependencies remain declared in `requirements.txt`.

## GitHub/Vercel
Upload this ZIP as the next commit on top of the deployed 1.10.9 source. Do not mix files from older Beta ZIPs.
