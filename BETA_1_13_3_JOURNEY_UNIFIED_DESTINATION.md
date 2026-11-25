# HDVIA BETA 1.13.3 – JOURNEY AI UNIFIED DESTINATION

- Removed the visible Điểm đến & thông tin module from primary/mobile navigation and home module links.
- Kept the destination catalog/API as an internal data capability for backward compatibility.
- `/destinations` and `/destinations/<slug>` now redirect into Hành Trình AI instead of exposing a separate destination UI.
- Hành Trình AI now enriches results with `destination_context` and renders destination overview, highlights, culture, history, food and best-for guidance in the same result screen.
- Added a Điểm đến tab inside Hành Trình AI.
- Existing Journey Intelligence weather, alerts, route and Plan B fields are preserved.


## Final deploy additions
- Unified `destination_context` into the core Journey result contract so web/API clients receive the same destination intelligence.
- Added Journey AI quality score and actionable completeness flags from the Journey Intelligence engine.
- Activated the existing per-day HDV briefing data in the Journey screen instead of leaving it as a placeholder.
- Fixed the Journey analysis tab grid for six sections (including Điểm đến) on desktop/mobile.
- Versioned the release as `1.13.3-unified-journey` and updated the health endpoint version.
