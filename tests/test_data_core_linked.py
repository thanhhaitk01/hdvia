import os,sys
sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
from data_core import COLLECTIONS,seed,resolve_context

def test_seed_has_all_eight_domains_and_linked_ids():
    s=seed()
    assert set(s)==set(COLLECTIONS)
    assert len(s['administrative'])==34
    assert len(s['destinations'])>=3
    assert all(r.get('admin_id') for r in s['destinations'])
    assert all(r.get('destination_id') for r in s['knowledge'])
    assert all(r.get('destination_id') for r in s['experiences'])
    assert all(r.get('destination_id') for r in s['weather_risk'])
    assert all(r.get('destination_ids') for r in s['journeys'])
    assert all(r.get('record_ref') for r in s['lineage'])

def test_journey_resolves_all_relevant_domains():
    g=resolve_context(seed(),journey_id='jny:da-nang-hoi-an-hue-4d')
    assert len(g['journeys'])==1
    assert {r['destination_id'] for r in g['destinations']}=={'dst:da-nang','dst:hoi-an','dst:hue'}
    assert {r['admin_id'] for r in g['administrative']}=={'adm:48','adm:46'}
    assert len(g['knowledge'])>=3
    assert len(g['experiences'])>=2
    assert len(g['weather_risk'])>=2
    assert len(g['market'])>=2
    assert len(g['lineage'])>=1

def test_destination_context_does_not_guess_unlinked_records():
    g=resolve_context(seed(),destination_id='dst:hue')
    assert {r['destination_id'] for r in g['destinations']}=={'dst:hue'}
    assert all(r['destination_id']=='dst:hue' for r in g['knowledge'])
    assert all(r['destination_id']=='dst:hue' for r in g['experiences'])
