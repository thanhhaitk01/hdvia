# HDVIA Beta 1.13.1 – Public Travel APIs

Adds a provider-neutral read-only gateway for 8 free/public travel API groups:
weather, geocoding, air quality, marine, OSM/Nominatim, OSRM routing, Wikipedia/Wikimedia, Wikidata, plus REST Countries reference data.

All external calls remain server-side. Provider attribution/rate-limit notes are retained in the catalog. No API secrets are hard-coded.

## Live credentials
REST Countries currently requires a bearer API key for its API. Other listed public endpoints are configured without a secret in this beta, subject to each provider's acceptable-use/rate-limit policies.

## Validation
The suite must pass before release. Network-dependent live calls are not claimed as passed when the test environment has no outbound DNS/network.
