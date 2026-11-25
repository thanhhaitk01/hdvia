"""HDVIA External World Connectivity (Beta 1.13 trial).

Four layers:
1) Two-way data sync with explicit provider adapters.
2) Provider integration lifecycle (connect/read/write/disconnect).
3) External AI/API orchestration with allowlisted endpoints and fallback.
4) Agent execution with permissions, dry-run by default and audit traces.

No provider secret is stored in source. Real provider credentials are injected
through environment variables/configuration at deployment time.
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import socket
import time
import urllib.parse
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Mapping, Optional, Protocol

from public_apis import PROVIDERS


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class ExternalWorldError(Exception):
    pass


@dataclass
class SyncResult:
    provider: str
    direction: str
    ok: bool
    records_read: int = 0
    records_written: int = 0
    skipped: int = 0
    error: str = ""
    trace_id: str = ""


class ProviderAdapter(Protocol):
    name: str
    capabilities: tuple[str, ...]

    def status(self) -> Dict[str, Any]: ...
    def connect(self, **kwargs: Any) -> Dict[str, Any]: ...
    def read(self, resource: str, **kwargs: Any) -> Dict[str, Any]: ...
    def write(self, resource: str, payload: Mapping[str, Any], **kwargs: Any) -> Dict[str, Any]: ...
    def disconnect(self, **kwargs: Any) -> Dict[str, Any]: ...


def _validate_public_url(url: str, *, allow_local: bool = False) -> str:
    p = urllib.parse.urlsplit(url)
    if p.scheme not in {"http", "https"} or not p.hostname:
        raise ExternalWorldError("Chỉ cho phép URL HTTP/HTTPS hợp lệ")
    host = p.hostname
    if allow_local and host in {"localhost", "127.0.0.1", "::1"}:
        return urllib.parse.urlunsplit((p.scheme, p.netloc, p.path or "/", p.query, ""))
    try:
        ip = ipaddress.ip_address(host)
        if not ip.is_global:
            raise ExternalWorldError("Từ chối đích private/reserved")
    except ValueError:
        try:
            infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise ExternalWorldError("Không phân giải được hostname") from exc
        for info in infos:
            addr = info[4][0]
            try:
                ip = ipaddress.ip_address(addr)
            except ValueError:
                continue
            if not ip.is_global:
                raise ExternalWorldError("Hostname trỏ vào mạng nội bộ/private/reserved")
    return urllib.parse.urlunsplit((p.scheme, p.netloc, p.path or "/", p.query, ""))


class HTTPProvider:
    """Small provider adapter for official/approved HTTP APIs.

    Endpoint and token are supplied at runtime. This makes the integration real
    without hard-coding credentials or pretending an OAuth flow exists when it
    has not been configured.
    """

    def __init__(self, name: str, *, base_url: str = "", token: str = "", enabled: bool = False,
                 capabilities: Iterable[str] = (), allow_local: bool = False, timeout: int = 15):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.enabled = bool(enabled and self.base_url)
        self.capabilities = tuple(capabilities)
        self.allow_local = allow_local
        self.timeout = timeout
        self._connected = False

    def status(self) -> Dict[str, Any]:
        return {"name": self.name, "enabled": self.enabled, "connected": self._connected,
                "capabilities": list(self.capabilities), "base_url_configured": bool(self.base_url)}

    def connect(self, **kwargs: Any) -> Dict[str, Any]:
        if not self.enabled:
            return {"ok": False, "provider": self.name, "error": "Provider chưa được cấu hình"}
        self._connected = True
        return {"ok": True, "provider": self.name, "connected": True, "time": utcnow()}

    def _request(self, method: str, resource: str, payload: Any = None) -> Dict[str, Any]:
        if not self.enabled:
            raise ExternalWorldError(f"Provider {self.name} chưa được cấu hình")
        url = resource if resource.startswith("http") else self.base_url + "/" + resource.lstrip("/")
        url = _validate_public_url(url, allow_local=self.allow_local)
        headers = {"Accept": "application/json", "User-Agent": "HDVIA-ExternalWorld/1.13"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        body = None
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=body, headers=headers, method=method.upper())
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read(2_000_001)
                if len(raw) > 2_000_000:
                    raise ExternalWorldError("Phản hồi provider vượt giới hạn")
                text = raw.decode(resp.headers.get_content_charset() or "utf-8", errors="replace")
                try:
                    data = json.loads(text) if text else {}
                except json.JSONDecodeError:
                    data = {"text": text[:12000]}
                return {"ok": True, "status_code": getattr(resp, "status", 200), "data": data}
        except urllib.error.HTTPError as exc:
            return {"ok": False, "status_code": exc.code, "error": f"Provider HTTP {exc.code}"}
        except (urllib.error.URLError, TimeoutError) as exc:
            return {"ok": False, "error": f"Provider network error: {exc}"}

    def read(self, resource: str, **kwargs: Any) -> Dict[str, Any]:
        return self._request("GET", resource)

    def write(self, resource: str, payload: Mapping[str, Any], **kwargs: Any) -> Dict[str, Any]:
        return self._request("POST", resource, dict(payload))

    def disconnect(self, **kwargs: Any) -> Dict[str, Any]:
        self._connected = False
        return {"ok": True, "provider": self.name, "connected": False, "time": utcnow()}


class ExternalWorldRegistry:
    def __init__(self, providers: Iterable[ProviderAdapter]):
        self._providers = {p.name: p for p in providers}

    def get(self, name: str) -> Optional[ProviderAdapter]:
        return self._providers.get((name or "").strip().lower())

    def status(self) -> list[Dict[str, Any]]:
        return [p.status() for p in self._providers.values()]

    def connect(self, name: str, **kwargs: Any) -> Dict[str, Any]:
        p = self.get(name)
        if not p:
            return {"ok": False, "error": "Provider không tồn tại"}
        return p.connect(**kwargs)

    def disconnect(self, name: str, **kwargs: Any) -> Dict[str, Any]:
        p = self.get(name)
        if not p:
            return {"ok": False, "error": "Provider không tồn tại"}
        return p.disconnect(**kwargs)


@dataclass
class SyncEngine:
    registry: ExternalWorldRegistry
    seen: set[str] = field(default_factory=set)

    def _id(self, provider: str, resource: str, record: Mapping[str, Any]) -> str:
        raw = json.dumps(record, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(f"{provider}|{resource}|{raw}".encode()).hexdigest()

    def pull(self, provider: str, resource: str, *, records_key: str = "records") -> SyncResult:
        trace = hashlib.sha256(f"{provider}|pull|{resource}|{utcnow()}".encode()).hexdigest()[:16]
        p = self.registry.get(provider)
        if not p:
            return SyncResult(provider, "pull", False, error="Provider không tồn tại", trace_id=trace)
        try:
            result = p.read(resource)
            if not result.get("ok"):
                return SyncResult(provider, "pull", False, error=str(result.get("error", "unknown")), trace_id=trace)
            data = result.get("data", {})
            records = data.get(records_key, data if isinstance(data, list) else [])
            if not isinstance(records, list):
                records = [records]
            fresh = 0
            for record in records:
                if isinstance(record, Mapping) and self._id(provider, resource, record) not in self.seen:
                    self.seen.add(self._id(provider, resource, record)); fresh += 1
            return SyncResult(provider, "pull", True, records_read=len(records), records_written=fresh, skipped=len(records)-fresh, trace_id=trace)
        except Exception as exc:
            return SyncResult(provider, "pull", False, error=str(exc)[:300], trace_id=trace)

    def push(self, provider: str, resource: str, records: Iterable[Mapping[str, Any]]) -> SyncResult:
        trace = hashlib.sha256(f"{provider}|push|{resource}|{utcnow()}".encode()).hexdigest()[:16]
        p = self.registry.get(provider)
        if not p:
            return SyncResult(provider, "push", False, error="Provider không tồn tại", trace_id=trace)
        written = 0
        try:
            for record in records:
                result = p.write(resource, record)
                if not result.get("ok"):
                    return SyncResult(provider, "push", False, records_written=written, error=str(result.get("error", "unknown")), trace_id=trace)
                written += 1
            return SyncResult(provider, "push", True, records_written=written, trace_id=trace)
        except Exception as exc:
            return SyncResult(provider, "push", False, records_written=written, error=str(exc)[:300], trace_id=trace)


class ExternalAIOrchestrator:
    """Provider-neutral orchestration with ordered fallback and bounded retries."""
    def __init__(self, providers: Mapping[str, ProviderAdapter], *, default_order: Iterable[str] = ()):
        self.providers = dict(providers)
        self.default_order = tuple(default_order)

    def run(self, task: str, payload: Mapping[str, Any], *, providers: Optional[Iterable[str]] = None,
            max_attempts: int = 2) -> Dict[str, Any]:
        order = tuple(providers or self.default_order or self.providers.keys())
        attempts = []
        for name in order:
            p = self.providers.get(name)
            if not p:
                continue
            for attempt in range(1, max_attempts + 1):
                result = p.write("/v1/tasks", {"task": task, "payload": dict(payload)})
                attempts.append({"provider": name, "attempt": attempt, "ok": bool(result.get("ok"))})
                if result.get("ok"):
                    return {"ok": True, "provider": name, "attempt": attempt, "result": result.get("data"), "attempts": attempts}
                if attempt < max_attempts:
                    time.sleep(0.05)
        return {"ok": False, "error": "Không có external AI provider phản hồi thành công", "attempts": attempts}


@dataclass
class AgentExecutionPolicy:
    allowed_tools: set[str] = field(default_factory=set)
    dry_run: bool = True


class AgentExecutor:
    def __init__(self, registry: ExternalWorldRegistry, *, audit_log: Optional[list[Dict[str, Any]]] = None):
        self.registry = registry
        self.audit_log = audit_log if audit_log is not None else []

    def execute(self, *, tool: str, provider: str, resource: str, payload: Mapping[str, Any],
                policy: AgentExecutionPolicy) -> Dict[str, Any]:
        trace = hashlib.sha256(f"{tool}|{provider}|{resource}|{utcnow()}".encode()).hexdigest()[:16]
        entry = {"trace_id": trace, "time": utcnow(), "tool": tool, "provider": provider, "resource": resource,
                 "dry_run": policy.dry_run, "status": "DENIED"}
        if tool not in policy.allowed_tools:
            entry["error"] = "Tool không được cấp quyền"
            self.audit_log.append(entry)
            raise ExternalWorldError("Tool không được cấp quyền")
        if policy.dry_run:
            entry["status"] = "DRY_RUN"
            self.audit_log.append(entry)
            return {"ok": True, "dry_run": True, "trace_id": trace, "action": tool}
        p = self.registry.get(provider)
        if not p:
            entry["error"] = "Provider không tồn tại"
            self.audit_log.append(entry)
            return {"ok": False, "trace_id": trace, "error": entry["error"]}
        result = p.write(resource, payload)
        entry["status"] = "EXECUTED" if result.get("ok") else "FAILED"
        entry["result"] = {"status_code": result.get("status_code"), "error": result.get("error", "")}
        self.audit_log.append(entry)
        return {"ok": bool(result.get("ok")), "dry_run": False, "trace_id": trace, "result": result}


def build_external_world_from_env() -> ExternalWorldRegistry:
    providers = []
    specs = (
        ("google", "HDVIA_GOOGLE_API_BASE", "HDVIA_GOOGLE_API_TOKEN", ("read", "write")),
        ("facebook", "HDVIA_FACEBOOK_API_BASE", "HDVIA_FACEBOOK_API_TOKEN", ("read", "write")),
        ("zalo", "HDVIA_ZALO_API_BASE", "HDVIA_ZALO_API_TOKEN", ("read", "write")),
        ("maps", "HDVIA_MAPS_API_BASE", "HDVIA_MAPS_API_TOKEN", ("route", "geocode")),
        ("external_ai", "HDVIA_EXTERNAL_AI_BASE", "HDVIA_EXTERNAL_AI_TOKEN", ("generate", "analyze")),
    )
    for name, base_key, token_key, caps in specs:
        base = os.environ.get(base_key, "").strip()
        token = os.environ.get(token_key, "").strip()
        providers.append(HTTPProvider(name, base_url=base, token=token, enabled=bool(base), capabilities=caps,
                                       allow_local=os.environ.get("HDVIA_EXTERNAL_ALLOW_LOCALHOST", "0") == "1"))
    # Public/read-only travel data providers. These require no secrets except
    # REST Countries, whose current API is bearer-token based.
    for name, public in PROVIDERS.items():
        providers.append(HTTPProvider(name, base_url=public.base_url, enabled=True, capabilities=("read",),
                                       timeout=12))
    return ExternalWorldRegistry(providers)
