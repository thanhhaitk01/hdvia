import os, sys, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data_acquisition import candidate_from_web, detect_kind, strip_html, source_type_for

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body=b"<html><head><title>Di san van hoa</title></head><body><p>Day la noi dung du lieu duoc cong bo boi nguon web de HDVIA thu thap va kiem chung truoc khi cong bo.</p></body></html>"
        self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self,*a): pass

def test_external_web_becomes_candidate_only(monkeypatch):
    monkeypatch.setenv("HDVIA_INGEST_ALLOW_LOCALHOST", "1")
    server=HTTPServer(("127.0.0.1",0),Handler); t=threading.Thread(target=server.serve_forever); t.daemon=True; t.start()
    try:
        item=candidate_from_web(url=f"http://127.0.0.1:{server.server_port}/x", requested_kind="knowledge")
        assert item["status"]=="CANDIDATE"
        assert item["kind"]=="knowledge"
        assert item["lineage"]["source_type"]=="WEB"
        assert item["record"]["source"].startswith("http://127.0.0.1")
    finally: server.shutdown(); t.join(timeout=2)

def test_detect_kind():
    assert detect_kind(requested="", title="Weather update", text="rain and wind") == "weather_risk"
    assert detect_kind(requested="", title="Inbound market", text="demand from India") == "market"

def test_strip_html():
    assert "noi dung" in strip_html("<script>x</script><p>noi dung</p>")

def test_source_type():
    assert source_type_for("https://example.gov.vn/a") == "OFFICIAL_GOVERNMENT"


def test_private_source_rejected(monkeypatch):
    monkeypatch.delenv("HDVIA_INGEST_ALLOW_LOCALHOST", raising=False)
    from data_acquisition import fetch_url
    try:
        fetch_url("http://127.0.0.1:9/")
    except ValueError as exc:
        assert "Từ chối" in str(exc)
    else:
        raise AssertionError("Private source must be rejected")
