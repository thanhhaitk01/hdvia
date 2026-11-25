# HDVIA Beta 1.13.2 — Journey Result Preservation Fix

## Fixed
- Prevented the Conversation Intelligence response from overwriting Journey Intelligence fields.
- Preserved `days`, `places`, `weather`, `risk_map`, `risks`, `plan_b`, and `briefing` after natural-language/weather queries.
- Fixed the Journey summary so destination names render cleanly instead of Python dictionary representations.
- Added a regression test for the conversation/Journey merge contract.

## Validation
- Full pytest suite: 90 passed.
