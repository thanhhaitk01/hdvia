from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_connect_modules_exist():
    assert (ROOT / "connect.py").exists()
    assert (ROOT / "connect_core.py").exists()
    assert (ROOT / "connectors.py").exists()


def test_connect_registry_is_provider_neutral():
    src = (ROOT / "connect_core.py").read_text(encoding="utf8")
    assert "ConnectorRegistry" in src
    assert "ConnectorDescriptor" in src
    assert "public_status" in src


def test_connector_lifecycle_contract_is_complete():
    src = (ROOT / "connectors.py").read_text(encoding="utf8")
    for method in ("status", "connect", "callback", "get_profile", "disconnect"):
        assert f"def {method}(" in src


def test_connect_status_endpoint_is_registered():
    src = (ROOT / "connect.py").read_text(encoding="utf8")
    assert "/status" in src
    assert "api/v1/connect" in src


def test_connect_provider_status_endpoint_is_registered():
    src = (ROOT / "connect.py").read_text(encoding="utf8")
    assert "<provider>/status" in src
    assert "registry.get(provider)" in src



def test_version_is_beta_19_connect_foundation():
    assert (ROOT / "VERSION").read_text(encoding="utf8").strip() == "1.11.0-open-data-agent"


def test_connect_health_and_dashboard_contracts():
    src=(ROOT/'connect.py').read_text(encoding='utf8')
    assert 'def connect_health(' in src
    assert 'def connect_dashboard(' in src
    assert '/health' in src
    assert '/dashboard' in src

def test_identity_linking_contract_exists():
    src=(ROOT/'app.py').read_text(encoding='utf8')
    for x in ['link_social_account','unlink_social_account','/account/connections','CONNECT_IDENTITY_LINKED','CONNECT_IDENTITY_UNLINKED']:
        assert x in src
