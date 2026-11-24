"""HDVIA autonomous open-data acquisition agent.

The agent fetches only from registered open/free sources, records provenance,
keeps every new record as CANDIDATE, and writes a local acquisition inbox.
It never auto-publishes data into the live knowledge warehouse.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from data_acquisition import candidate_from_web, USER_AGENT
from source_registry import SOURCES, allowed_for_auto, get_source

ROOT = Path(__file__).resolve().parent
INBOX = ROOT / "data" / "acquisition" / "candidates.json"
STATE = ROOT / "data" / "acquisition" / "state.json"

DEFAULT_TARGETS = [
    "Hà Nội", "Cao Bằng", "Tuyên Quang", "Điện Biên", "Lai Châu", "Sơn La",
    "Lào Cai", "Thái Nguyên", "Lạng Sơn", "Quảng Ninh", "Bắc Ninh", "Phú Thọ",
    "Hải Phòng", "Hưng Yên", "Ninh Bình", "Thanh Hóa", "Nghệ An", "Hà Tĩnh",
    "Quảng Trị", "Huế", "Đà Nẵng", "Quảng Ngãi", "Gia Lai", "Khánh Hòa",
    "Đắk Lắk", "Lâm Đồng", "Đồng Nai", "Thành phố Hồ Chí Minh", "Tây Ninh",
    "Đồng Tháp", "Vĩnh Long", "An Giang", "Cần Thơ", "Cà Mau",
    "Hội An", "Phong Nha", "Mỹ Sơn", "Sơn Trà", "Lăng Khải Định", "Bà Nà Hills",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_key(source_id: str, url: str, title: str, text: str) -> str:
    raw = f"{source_id}\n{url}\n{title}\n{text}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _api_json(url: str, *, timeout: int = 20) -> dict:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read(2_000_000).decode(resp.headers.get_content_charset() or "utf-8"))


def wikimedia_search_extract(query: str) -> list[dict]:
    base = get_source("wikimedia_vi")["base_url"]
    params = {
        "action": "query", "format": "json", "formatversion": "2",
        "list": "search", "srsearch": query, "srlimit": "3",
    }
    search = _api_json(base + "?" + urllib.parse.urlencode(params))
    titles = [x.get("title") for x in search.get("query", {}).get("search", []) if x.get("title")]
    if not titles:
        return []
    params = {
        "action": "query", "format": "json", "formatversion": "2",
        "prop": "extracts|info", "explaintext": "1", "exintro": "1",
        "inprop": "url", "titles": "|".join(titles),
    }
    data = _api_json(base + "?" + urllib.parse.urlencode(params))
    pages = data.get("query", {}).get("pages", [])
    out = []
    for p in pages:
        text = (p.get("extract") or "").strip()
        if len(text) >= 80:
            out.append({"title": p.get("title", query), "text": text[:12000], "url": p.get("fullurl") or "https://vi.wikipedia.org/wiki/" + urllib.parse.quote(p.get("title", "").replace(" ", "_"))})
    return out


def nominatim_search(query: str) -> list[dict]:
    base = get_source("nominatim_osm")["base_url"]
    params = {"q": query + ", Việt Nam", "format": "jsonv2", "limit": "1", "addressdetails": "1", "accept-language": "vi"}
    return _api_json(base + "?" + urllib.parse.urlencode(params))


def make_wikimedia_candidate(target: str, page: dict) -> dict:
    url, title, text = page["url"], page["title"], page["text"]
    key = stable_key("wikimedia_vi", url, title, text)
    return {
        "candidate_id": "acq:" + key[:20],
        "source_id": "wikimedia_vi",
        "source_type": "OPEN_API",
        "source": url,
        "license": SOURCES["wikimedia_vi"]["license"],
        "attribution": SOURCES["wikimedia_vi"]["attribution"],
        "collected_at": now(),
        "target": target,
        "kind": "knowledge",
        "status": "CANDIDATE",
        "title": title,
        "content": text,
        "confidence": "UNASSESSED",
        "content_digest": key,
    }


def make_osm_candidate(target: str, row: dict) -> dict:
    url = "https://www.openstreetmap.org/?mlat={}&mlon={}#map=16/{}/{}".format(row.get("lat"), row.get("lon"), row.get("lat"), row.get("lon"))
    key = stable_key("nominatim_osm", url, target, json.dumps(row, ensure_ascii=False, sort_keys=True))
    return {
        "candidate_id": "acq:" + key[:20],
        "source_id": "nominatim_osm",
        "source_type": "OPEN_DATA_API",
        "source": url,
        "license": SOURCES["nominatim_osm"]["license"],
        "attribution": SOURCES["nominatim_osm"]["attribution"],
        "collected_at": now(),
        "target": target,
        "kind": "destinations",
        "status": "CANDIDATE",
        "title": row.get("display_name", target),
        "content": json.dumps({"lat": row.get("lat"), "lon": row.get("lon"), "type": row.get("type"), "class": row.get("class"), "address": row.get("address", {})}, ensure_ascii=False),
        "confidence": "UNASSESSED",
        "content_digest": key,
    }


def run(targets: list[str] | None = None) -> dict:
    targets = targets or DEFAULT_TARGETS
    inbox = load_json(INBOX, {"version": "1.0.0", "records": []})
    records = inbox.get("records", [])
    known = {r.get("content_digest") for r in records}
    state = load_json(STATE, {"last_run": None, "sources": {}})
    stats = {"targets": len(targets), "new": 0, "duplicates": 0, "errors": []}

    # Wikimedia: one small search per target, sequentially, with a polite delay.
    if allowed_for_auto("wikimedia_vi"):
        for target in targets:
            try:
                for page in wikimedia_search_extract(target):
                    rec = make_wikimedia_candidate(target, page)
                    if rec["content_digest"] in known:
                        stats["duplicates"] += 1
                    else:
                        records.append(rec); known.add(rec["content_digest"]); stats["new"] += 1
            except Exception as exc:
                stats["errors"].append({"source": "wikimedia_vi", "target": target, "error": str(exc)[:300]})
            time.sleep(get_source("wikimedia_vi")["rate_limit_seconds"])

    # Nominatim is deliberately capped per run because its public service is capacity-limited.
    osm_targets = targets[: int(get_source("nominatim_osm")["max_requests_per_run"])]
    if allowed_for_auto("nominatim_osm"):
        for target in osm_targets:
            try:
                rows = nominatim_search(target)
                for row in rows:
                    rec = make_osm_candidate(target, row)
                    if rec["content_digest"] in known:
                        stats["duplicates"] += 1
                    else:
                        records.append(rec); known.add(rec["content_digest"]); stats["new"] += 1
            except Exception as exc:
                stats["errors"].append({"source": "nominatim_osm", "target": target, "error": str(exc)[:300]})
            time.sleep(get_source("nominatim_osm")["rate_limit_seconds"])

    # Keep the inbox bounded so autonomous collection cannot grow without limit.
    max_records = int(os.environ.get("HDVIA_ACQ_MAX_RECORDS", "5000"))
    inbox["records"] = records[-max_records:]
    inbox["updated_at"] = now()
    save_json(INBOX, inbox)
    state["last_run"] = now()
    state["last_stats"] = stats
    save_json(STATE, state)
    return stats


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", action="append", dest="targets")
    args = parser.parse_args()
    print(json.dumps(run(args.targets), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
