import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from external_world import (HTTPProvider, ExternalWorldRegistry, SyncEngine,
                             ExternalAIOrchestrator, AgentExecutor, AgentExecutionPolicy,
                             ExternalWorldError)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"records": [{"id": 1, "name": "Hue"}]}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(body)
    def do_POST(self):
        n = int(self.headers.get("Content-Length", "0")); raw = self.rfile.read(n)
        body = json.dumps({"received": json.loads(raw or b"{}"), "ok": True}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(body)
    def log_message(self, *_): pass


def server():
    s = HTTPServer(("127.0.0.1", 0), Handler); t = threading.Thread(target=s.serve_forever, daemon=True); t.start(); return s


def test_two_way_sync_and_dedup():
    s = server()
    try:
        p = HTTPProvider("mock", base_url=f"http://127.0.0.1:{s.server_port}", enabled=True, allow_local=True, capabilities=("read", "write"))
        reg = ExternalWorldRegistry([p]); p.connect()
        sync = SyncEngine(reg)
        first = sync.pull("mock", "/records")
        second = sync.pull("mock", "/records")
        pushed = sync.push("mock", "/records", [{"id": 2, "name": "Da Nang"}])
        assert first.ok and first.records_read == 1 and first.records_written == 1
        assert second.ok and second.records_written == 0 and second.skipped == 1
        assert pushed.ok and pushed.records_written == 1
    finally: s.shutdown()


def test_provider_lifecycle_is_real_not_contract_placeholder():
    s = server()
    try:
        p = HTTPProvider("mock", base_url=f"http://127.0.0.1:{s.server_port}", enabled=True, allow_local=True)
        assert p.connect()["ok"] is True
        assert p.status()["connected"] is True
        assert p.write("/x", {"hello": "world"})["ok"] is True
        assert p.disconnect()["connected"] is False
    finally: s.shutdown()


def test_external_ai_orchestration_fallback():
    s = server()
    try:
        p = HTTPProvider("mock", base_url=f"http://127.0.0.1:{s.server_port}", enabled=True, allow_local=True)
        o = ExternalAIOrchestrator({"mock": p}, default_order=("mock",))
        result = o.run("analyze", {"journey": "Hue"})
        assert result["ok"] is True and result["provider"] == "mock"
    finally: s.shutdown()


def test_agent_execution_permission_and_dry_run():
    p = HTTPProvider("mock", base_url="https://example.com", enabled=False)
    reg = ExternalWorldRegistry([p]); audit = []; ex = AgentExecutor(reg, audit_log=audit)
    policy = AgentExecutionPolicy(allowed_tools={"calendar.write"}, dry_run=True)
    result = ex.execute(tool="calendar.write", provider="mock", resource="/events", payload={"x": 1}, policy=policy)
    assert result["ok"] and result["dry_run"] and audit[-1]["status"] == "DRY_RUN"
    try:
        ex.execute(tool="email.send", provider="mock", resource="/send", payload={}, policy=policy)
        assert False, "permission should fail"
    except ExternalWorldError:
        pass
