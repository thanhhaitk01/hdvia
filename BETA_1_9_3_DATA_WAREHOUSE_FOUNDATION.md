# HDVIA BETA 1.9.3 — DATA WAREHOUSE FOUNDATION

Baseline: HDVIA Beta 1.9.2 Journey UI Fix.

## Scope
- Central data warehouse schema for destinations, knowledge, guide scripts, guide experiences and media.
- Admin UI: Quản trị → Kho dữ liệu HDVIA.
- Structured record validation and SQLite runtime storage.
- JSON export endpoints for promotion of curated runtime data into the repository's canonical data layer.
- Public read API for records marked `PUBLISHED` or `ACTIVE`.
- Existing 34-province and destination catalog remain unchanged.

## Important deployment note
The Beta runtime database follows the existing `/tmp/hdvia/data/hdvia.db` model used by the Vercel deployment. Runtime records are therefore not a permanent GitHub datastore. Use the JSON export from the admin page to review and promote curated data into the repository's `data/warehouse/` source files before productionizing persistent storage.

## Regression
- Baseline tests: 45/45 PASS before 1.9.3 changes.
- New warehouse tests are included in `tests/test_data_warehouse.py`.
