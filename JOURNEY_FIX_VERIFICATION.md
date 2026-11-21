# HDVIA V1.5 Journey Fix — verified package

## Fixed
- Journey Engine version was still reporting `1.4.0`; corrected to `1.5.0`.
- `generated_at` now uses timezone-aware UTC timestamps.
- Journey UI previously rendered weather only for the first detected place even though the engine calculated weather for every place. The UI now renders the 7-day forecast for every detected itinerary place.
- Added the missing `vercel.json` required by the repository smoke test/deployment configuration.
- Added regression tests for per-place 7-day weather, engine version, and journey weather rendering.

## Verification
- `pytest -q`: **6 passed**
- All Python files compile successfully.
