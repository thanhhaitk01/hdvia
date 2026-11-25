from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from public_apis import PROVIDERS, weather, geocode, air_quality, marine, search_place, route, wikipedia_search, wikidata_search, country


def test_eight_travel_api_groups_registered():
    expected = {"open_meteo","open_meteo_geocoding","open_meteo_air_quality","open_meteo_marine","osm_nominatim","osrm","wikipedia","wikidata","rest_countries"}
    assert expected.issubset(PROVIDERS.keys())


def test_provider_urls_are_https_and_named():
    for p in PROVIDERS.values():
        assert p.base_url.startswith("https://")
        assert p.name


def test_request_builders_expose_normalized_functions():
    for fn in (weather, geocode, air_quality, marine, search_place, route, wikipedia_search, wikidata_search, country):
        assert callable(fn)
