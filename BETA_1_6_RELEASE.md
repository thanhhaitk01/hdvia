# HDVIA Beta 1.6

## Baseline
Fresh build from the verified HDVIA V1.5 Journey baseline. Existing UI, routes and functions are retained.

## Added
- Journey Intelligence Engine 1.6.0
- Tour Briefing by day
- Plan B by day based on detected risk
- Confidence indicator for analysis completeness
- Journey feedback API and UI
- Feedback is stored separately and is not automatically promoted into the Knowledge Base
- Health endpoint reports Beta 1.6 modules

## Verification
- pytest: 10 passed
- Python compileall: passed
- Existing route contract checks: passed
- Journey multi-place weather contract: passed
- 7-day weather contract per detected place: passed

## Deployment
This package is intended as a clean replacement for the current GitHub repository contents. Do not merge it file-by-file with older packages.
