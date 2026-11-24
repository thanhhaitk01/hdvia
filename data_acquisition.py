"""HDVIA external data acquisition layer.

Fetches only from configured/explicit sources, extracts a bounded text payload,
and sends it through the existing LearningPipeline as CANDIDATE. It never
publishes external content automatically.
"""
from __future__ import annotations
import hashlib, html, json, os, re, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from data_core import COLLECTIONS, LearningPipeline, ID_FIELDS

USER_AGENT = os.environ.get("HDVIA_INGEST_USER_AGENT", "HDVIA-DataAcquisition/1.0 (+https://hdvia.vn)")
MAX_BYTES = int(os.environ.get("HDVIA_INGEST_MAX_BYTES", "1000000"))
TIMEOUT = int(os.environ.get("HDVIA_INGEST_TIMEOUT", "15"))


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def canonical_url(url: str) -> str:
    p = urllib.parse.urlsplit(url.strip())
    return urllib.parse.urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path or "/", p.query, ""))


def source_type_for(url: str) -> str:
    host = urllib.parse.urlsplit(url).netloc.lower()
    if host.endswith(".gov.vn") or host == "gov.vn":
        return "OFFICIAL_GOVERNMENT"
    if "google." in host:
        return "SEARCH_PROVIDER"
    return "WEB"


def fetch_url(url: str, *, timeout: int = TIMEOUT, max_bytes: int = MAX_BYTES) -> Dict[str, Any]:
    p = urllib.parse.urlsplit(url)
    if p.scheme not in ("http", "https"):
        raise ValueError("Chỉ cho phép nguồn HTTP/HTTPS")
    req = urllib.request.Request(canonical_url(url), headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get("Content-Type", "")
            data = resp.read(max_bytes + 1)
            if len(data) > max_bytes:
                raise ValueError("Nguồn vượt giới hạn kích thước ingest")
            charset = resp.headers.get_content_charset() or "utf-8"
            return {"url": canonical_url(url), "status_code": getattr(resp, "status", 200), "content_type": content_type, "text": data.decode(charset, errors="replace")}
    except urllib.error.HTTPError as exc:
        raise ValueError(f"Nguồn trả HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"Không truy cập được nguồn: {exc.reason}") from exc


def strip_html(raw: str) -> str:
    raw = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", raw)
    raw = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", raw)
    raw = re.sub(r"(?is)<noscript[^>]*>.*?</noscript>", " ", raw)
    raw = re.sub(r"(?is)<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw


def extract_title(raw: str) -> str:
    m = re.search(r"(?is)<title[^>]*>(.*?)</title>", raw)
    return re.sub(r"\s+", " ", html.unescape(m.group(1))).strip() if m else ""


def extract_text(payload: Dict[str, Any]) -> str:
    text = payload.get("text", "")
    ctype = payload.get("content_type", "")
    if "application/json" in ctype:
        try:
            obj = json.loads(text)
            text = json.dumps(obj, ensure_ascii=False)
        except Exception:
            pass
    return strip_html(text)[:12000]


def detect_kind(*, requested: str, title: str, text: str) -> str:
    if requested in COLLECTIONS:
        return requested
    hay = f"{title} {text}".lower()
    if any(x in hay for x in ("thời tiết", "weather", "mưa", "bão", "gió", "nhiệt độ")):
        return "weather_risk"
    if any(x in hay for x in ("thị trường", "du khách", "khách quốc tế", "market", "demand")):
        return "market"
    if any(x in hay for x in ("kinh nghiệm", "hướng dẫn viên", "guide", "tour guide")):
        return "experiences"
    if any(x in hay for x in ("hành trình", "itinerary", "tour ", "lịch trình")):
        return "journeys"
    return "knowledge"


def candidate_from_web(*, url: str, requested_kind: str = "knowledge", destination_id: str = "", admin_id: str = "") -> Dict[str, Any]:
    fetched = fetch_url(url)
    title = extract_title(fetched["text"]) or urllib.parse.urlsplit(fetched["url"]).netloc
    text = extract_text(fetched)
    if len(text) < 40:
        raise ValueError("Nguồn không đủ nội dung để tạo candidate")
    kind = detect_kind(requested=requested_kind, title=title, text=text)
    digest = hashlib.sha256((fetched["url"] + "\n" + text).encode("utf-8")).hexdigest()[:16]
    payload: Dict[str, Any]
    if kind == "knowledge":
        payload = {"knowledge_id": f"kn:web-{digest}", "destination_id": destination_id or None, "admin_id": admin_id or None, "title": title[:240], "place": title[:120], "topic": "external-web", "content": text, "source": fetched["url"], "confidence": "UNASSESSED", "status": "CANDIDATE"}
    elif kind == "experiences":
        payload = {"experience_id": f"exp:web-{digest}", "destination_id": destination_id or None, "admin_id": admin_id or None, "title": title[:240], "place": title[:120], "season": "", "risk_level": "UNASSESSED", "content": text, "source": fetched["url"], "confidence": "UNASSESSED", "status": "CANDIDATE"}
    elif kind == "market":
        payload = {"market_id": f"mkt:web-{digest}", "destination_id": destination_id or None, "admin_id": admin_id or None, "segment": "EXTERNAL", "market": "UNASSESSED", "insight": text, "source": fetched["url"], "confidence": "UNASSESSED", "status": "CANDIDATE"}
    elif kind == "weather_risk":
        payload = {"risk_id": f"risk:web-{digest}", "destination_id": destination_id or None, "admin_id": admin_id or None, "location_code": admin_id or "UNKNOWN", "observed_at": now(), "forecast_type": "EXTERNAL_CANDIDATE", "risk_level": "UNASSESSED", "hazards": [], "plan_b": "", "source": fetched["url"], "status": "CANDIDATE"}
    elif kind == "journeys":
        payload = {"journey_id": f"jny:web-{digest}", "destination_ids": [destination_id] if destination_id else [], "title": title[:240], "locations": [], "duration_days": 0, "traveler_profile": "", "transport": "", "issues": [], "solutions": [], "source": fetched["url"], "status": "CANDIDATE"}
    else:
        payload = {"knowledge_id": f"kn:web-{digest}", "destination_id": destination_id or None, "admin_id": admin_id or None, "title": title[:240], "place": title[:120], "topic": "external-web", "content": text, "source": fetched["url"], "confidence": "UNASSESSED", "status": "CANDIDATE"}
        kind = "knowledge"
    item = LearningPipeline().ingest(kind=kind, payload=payload, source=fetched["url"], source_type=source_type_for(fetched["url"]))
    item["fetch"] = {k: fetched[k] for k in ("url", "status_code", "content_type")}
    item["content_digest"] = digest
    return item


def google_cse_search(query: str, *, num: int = 5) -> List[Dict[str, Any]]:
    """Use Google's official Custom Search JSON API when credentials are configured.
    No Google HTML scraping is performed.
    """
    key = os.environ.get("GOOGLE_CSE_API_KEY", "").strip()
    cx = os.environ.get("GOOGLE_CSE_CX", "").strip()
    if not key or not cx:
        raise RuntimeError("Thiếu GOOGLE_CSE_API_KEY hoặc GOOGLE_CSE_CX")
    qs = urllib.parse.urlencode({"key": key, "cx": cx, "q": query, "num": max(1, min(10, int(num)))})
    raw = fetch_url("https://www.googleapis.com/customsearch/v1?" + qs)
    try:
        data = json.loads(raw["text"])
    except json.JSONDecodeError as exc:
        raise ValueError("Google CSE trả dữ liệu không hợp lệ") from exc
    return [{"title": x.get("title", ""), "url": x.get("link", ""), "snippet": x.get("snippet", "")} for x in data.get("items", []) if x.get("link")]


def source_manifest() -> Dict[str, Any]:
    return {"version": "1.0.0", "connectors": [
        {"id": "web", "mode": "explicit_url", "status": "READY"},
        {"id": "google_cse", "mode": "official_api", "status": "READY_IF_CONFIGURED"},
        {"id": "official_gov", "mode": "explicit_url", "status": "READY"},
    ], "publication_policy": "CANDIDATE_ONLY"}
