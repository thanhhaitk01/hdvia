from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_self_update_job_endpoint_and_queue_exist():
    src=(ROOT/'app.py').read_text(encoding='utf8')
    assert 'knowledge_update_jobs' in src
    assert '/api/v1/self-update/run' in src
    assert 'HDVIA_SELF_UPDATE_CRON_TOKEN' in src
    assert 'self_update_engine.enrich' in src

def test_scheduled_runner_contract_exists():
    wf=ROOT/'.github/workflows/hdvia-self-update.yml'
    assert wf.exists()
    text=wf.read_text(encoding='utf8')
    assert 'schedule:' in text and 'HDVIA_SELF_UPDATE_URL' in text and 'HDVIA_SELF_UPDATE_CRON_TOKEN' in text
