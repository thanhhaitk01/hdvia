# HDVIA 1.11.0 — Open Data First

HDVIA no longer requires a Google Maps subscription for its base open-data integration.

## Connectors
- OpenStreetMap/Nominatim: end-user place lookup, attribution, rate-limited; no API key.
- GeoNames: free web service with a free account username, plus daily downloadable open data.
- Existing official-government URL ingestion remains available.

## Safety/data governance
External results are context only until they enter the existing `CANDIDATE → REVIEW → PUBLISHED` pipeline. No automatic publication.

Nominatim is deliberately not used for autocomplete, systematic/bulk POI harvesting, or high-volume background polling. The connector follows the public service policy.
