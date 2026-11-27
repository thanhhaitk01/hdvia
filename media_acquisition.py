"""HDVIA media acquisition runner for the 6-layer data fusion pipeline.

It collects candidate image metadata from open/licensed APIs, scores them with
VerifiedImageResolver, and writes only verified metadata to the media index.
The live application can still fail closed when a verified image is unavailable.
"""
from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List

from api_adapters import OpenAPIAdapter
from entity_resolution import EntityResolver
from image_entity_resolution import VerifiedImageResolver
from media_warehouse import build_media_record, upsert_records
from official_source_discovery import discover_official_sources

DEFAULT_TARGETS = [
    "Chùa Cầu Hội An", "Phố cổ Hội An", "Mỹ Sơn", "Bà Nà Hills", "Sơn Trà",
    "Đà Nẵng", "Huế", "Hà Nội", "Hạ Long", "Phong Nha"
]


def run(targets: List[str]) -> Dict[str, Any]:
    adapter = OpenAPIAdapter()
    entity_resolver = EntityResolver(adapter)
    image_resolver = VerifiedImageResolver(adapter)
    records = []
    stats = {"targets": len(targets), "verified": 0, "rejected": 0, "errors": []}
    for name in targets:
        try:
            entity = entity_resolver.resolve(name)
            lat = lon = None
            geo = adapter.geocode(name)
            rows = ((geo.get("data") or {}).get("results") or []) if geo.get("ok") else []
            if rows:
                lat, lon = rows[0].get("latitude"), rows[0].get("longitude")
            result = image_resolver.resolve(name, entity=entity, lat=lat, lon=lon)
            if not result.get("ok") and entity.get("confidence") in {"HIGH", "MEDIUM"}:
                # Official/local tourism discovery is optional and review-safe.
                # Discovered pages are candidates; they are never auto-published
                # merely because the page returned an image.
                official = discover_official_sources(name, limit=3)
                for src in official:
                    if src.get("image_url"):
                        candidate = {
                            "url": src["image_url"], "title": src.get("title"),
                            "description": src.get("snippet", ""), "_source": "official_source",
                            "source_url": src.get("url"),
                        }
                        score, evidence = image_resolver._candidate_score(
                            candidate, name, image_resolver._aliases(name, entity), lat, lon,
                            image_resolver._wikidata_id(entity), direct_entity=False, geo_source=False)
                        if score >= image_resolver.ACCEPT_CONFIDENCE:
                            result = {
                                "ok": True, "name": name, "image_url": candidate["url"],
                                "confidence": "HIGH", "score": round(score, 1),
                                "title": candidate.get("title"), "source": "official_source",
                                "source_url": candidate.get("source_url"),
                                "entity_id": image_resolver._wikidata_id(entity),
                                "evidence": evidence, "resolver_version": image_resolver.VERSION,
                                "provenance": {"source": "official_source", "license": "REVIEW_REQUIRED"},
                            }
                            break
            if result.get("ok"):
                record = build_media_record(
                    entity_id=str(result.get("entity_id") or ""), entity_name=name,
                    candidate={
                        "url": result.get("image_url"), "title": result.get("title"),
                        "license": (result.get("provenance") or {}).get("license"),
                        "_source": result.get("source"), "source_url": result.get("source_url"),
                    }, score=result.get("score", 0), confidence=result.get("confidence", "LOW"),
                    evidence=result.get("evidence") or {},
                )
                records.append(record); stats["verified"] += 1
            else:
                stats["rejected"] += 1
        except Exception as exc:
            stats["errors"].append({"target": name, "error": str(exc)[:300]})
    if records:
        stats["warehouse"] = upsert_records(records)
    return stats


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", action="append", dest="targets")
    args = parser.parse_args()
    print(json.dumps(run(args.targets or DEFAULT_TARGETS), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
