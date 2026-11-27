"""Discover official/local tourism pages and their image metadata.

Discovery is optional and credential-gated through Google CSE. The module never
scrapes search-result HTML and never treats a discovered page as verified data.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List
from urllib.parse import urlsplit

from data_acquisition import fetch_url, google_cse_search

ALLOWED_DOMAINS = (
    "dt.gov.vn", "vietnamtourism.gov.vn", "nentangso.vietnamtourism.gov.vn",
    "danang.gov.vn", "hoian.gov.vn", "hue.gov.vn", "quangngai.gov.vn",
)


def _allowed(url: str) -> bool:
    host = (urlsplit(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in ALLOWED_DOMAINS)


def _og_image(html: str) -> str:
    for pattern in (
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image',
    ):
        m = re.search(pattern, html, flags=re.I)
        if m:
            return m.group(1).strip()
    return ""


def discover_official_sources(name: str, limit: int = 5) -> List[Dict[str, Any]]:
    if not os.getenv("GOOGLE_CSE_API_KEY") or not os.getenv("GOOGLE_CSE_CX"):
        return []
    rows = google_cse_search(f'"{name}" (du lịch OR điểm đến OR di tích)', num=limit)
    out = []
    for row in rows:
        url = row.get("url", "")
        if not _allowed(url):
            continue
        try:
            fetched = fetch_url(url)
            image = _og_image(fetched.get("text", ""))
        except Exception:
            image = ""
        out.append({
            "source": "official_source",
            "url": url,
            "title": row.get("title", ""),
            "snippet": row.get("snippet", ""),
            "image_url": image,
            "source_domain": urlsplit(url).netloc.lower(),
            "verified": False,
        })
    return out
