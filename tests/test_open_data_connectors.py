import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import open_data_connectors as od

class FakeResponse:
    def __init__(self, payload):
        self.payload=payload
        self.headers=self

    def __enter__(self): return self
    def __exit__(self,*a): pass
    def read(self): return json.dumps(self.payload).encode()
    def get_content_charset(self): return 'utf-8'
    def get(self, key, default=None): return default

def test_status_is_open_data_first(monkeypatch):
    monkeypatch.delenv('GEONAMES_USERNAME', raising=False)
    s=od.open_data_status()
    assert s['providers']['osm_nominatim']['api_key_required'] is False
    assert s['providers']['geonames_download']['enabled'] is True

def test_osm_normalizes_results(monkeypatch):
    monkeypatch.setattr(od.urllib.request, 'urlopen', lambda *a, **k: FakeResponse([{'osm_type':'node','osm_id':1,'name':'Đà Nẵng','display_name':'Đà Nẵng, Việt Nam','lat':'16.05','lon':'108.2','type':'city','category':'place','address':{'city':'Đà Nẵng'}}]))
    monkeypatch.setattr(od.time, 'monotonic', lambda: 100.0)
    monkeypatch.setattr(od.time, 'sleep', lambda _: None)
    od._last_nominatim_call=0
    r=od.osm_nominatim_search('Đà Nẵng')
    assert r['provider']=='osm_nominatim'
    assert r['results'][0]['name']=='Đà Nẵng'
    assert r['attribution']=='© OpenStreetMap contributors'

def test_geonames_normalizes_results(monkeypatch):
    monkeypatch.setenv('GEONAMES_USERNAME','testuser')
    monkeypatch.setattr(od.urllib.request, 'urlopen', lambda *a, **k: FakeResponse({'geonames':[{'geonameId':123,'name':'Hue','lat':'16.46','lng':'107.59','fcl':'P','fcode':'PPLA','countryCode':'VN','adminName1':'Huế','population':500000}]}))
    r=od.geonames_search('Huế')
    assert r['provider']=='geonames'
    assert r['results'][0]['geoname_id']==123
    assert r['results'][0]['country_code']=='VN'

def test_geonames_requires_username(monkeypatch):
    monkeypatch.delenv('GEONAMES_USERNAME', raising=False)
    try: od.geonames_search('Huế')
    except ValueError as exc: assert 'GEONAMES_USERNAME' in str(exc)
    else: raise AssertionError('GeoNames username must be required for web service')
