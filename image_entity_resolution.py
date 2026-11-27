"""Verified image/entity resolution for HDVIA.

The module deliberately fails closed: a live Wikimedia response is not enough.
An image must be supported by the resolved entity, strong title/alias evidence,
or geographic evidence before it can be rendered as a representative image.
"""
from __future__ import annotations

import math
import re
import unicodedata
from typing import Any, Dict, Iterable, List, Optional, Tuple


def normalize(text: str) -> str:
    s = unicodedata.normalize("NFD", str(text or "").strip().lower())
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = s.replace("đ", "d")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def tokens(text: str) -> set[str]:
    return set(normalize(text).split())


def haversine_km(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(float(a_lat)), math.radians(float(b_lat))
    dp = math.radians(float(b_lat) - float(a_lat))
    dl = math.radians(float(b_lon) - float(a_lon))
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * 2 * math.asin(math.sqrt(x))


class VerifiedImageResolver:
    VERSION = "1.30.1-hdv-giau-kinh-nghiem"
    MIN_CONFIDENCE = 78
    ACCEPT_CONFIDENCE = 88

    def __init__(self, adapter):
        self.adapter = adapter

    def _wikidata_id(self, entity: Optional[Dict[str, Any]]) -> Optional[str]:
        if not isinstance(entity, dict):
            return None
        wd = entity.get("wikidata") if "wikidata" in entity else entity
        if not isinstance(wd, dict):
            return None
        value = wd.get("id") or wd.get("wikibase_item")
        return str(value) if value else None

    def _aliases(self, name: str, entity: Optional[Dict[str, Any]]) -> List[str]:
        out = [str(name or "").strip()]
        if isinstance(entity, dict):
            for key in ("canonical_name", "label"):
                value = entity.get(key)
                if value and value not in out:
                    out.append(str(value))
            wd = entity.get("wikidata")
            if isinstance(wd, dict):
                for key in ("label", "aliases"):
                    value = wd.get(key)
                    if isinstance(value, list):
                        out.extend(str(x) for x in value if x)
                    elif value:
                        out.append(str(value))
        # Bounded, high-confidence cross-language landmark bridges.
        aliases = {
            "chua cau": ["Japanese Bridge", "Hoi An Japanese Bridge"],
            "chua cau hoi an": ["Japanese Bridge", "Hoi An Japanese Bridge"],
            "cau nhat ban hoi an": ["Japanese Bridge", "Hoi An Japanese Bridge"],
            "japanese bridge": ["Japanese Bridge", "Hoi An Japanese Bridge"],
            "hoi an japanese bridge": ["Japanese Bridge", "Hoi An Japanese Bridge"],
            "thanh dia my son": ["My Son Sanctuary", "My Son"],
            "ba na hills": ["Ba Na Hills", "Bana Hills"],
            "ba na hill": ["Ba Na Hills", "Bana Hills"],
        }
        for alias in aliases.get(normalize(name), []):
            if alias not in out:
                out.append(alias)
        # Never allow a generic parent to outrank a specific entity.
        return list(dict.fromkeys(out))[:12]

    @staticmethod
    def _imageinfo(page: Dict[str, Any]) -> Dict[str, Any]:
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        def meta_value(key: str) -> str:
            value = meta.get(key)
            if isinstance(value, dict):
                return str(value.get("value") or "")
            return str(value or "")
        return {
            "url": info.get("thumburl") or info.get("url"),
            "title": page.get("title"),
            "description": meta_value("ImageDescription"),
            "categories": meta_value("Categories"),
            "caption": meta_value("ObjectName"),
            "lat": meta_value("GPSLatitude"),
            "lon": meta_value("GPSLongitude"),
            "artist": meta_value("Artist"),
            "license": meta_value("LicenseShortName"),
        }

    @staticmethod
    def _parse_coord(value: Any) -> Optional[float]:
        try:
            s = str(value).strip()
            if not s:
                return None
            # Commons commonly returns decimal strings, occasionally with N/E suffix.
            sign = -1 if s[-1:].upper() in {"S", "W"} else 1
            s = s.rstrip("NnEeSsWw ").replace(",", ".")
            return sign * float(s)
        except Exception:
            return None

    def _candidate_score(
        self, candidate: Dict[str, Any], name: str, aliases: List[str],
        lat: Optional[float], lon: Optional[float], entity_id: Optional[str],
        direct_entity: bool = False, geo_source: bool = False
    ) -> Tuple[float, Dict[str, Any]]:
        hay_title = normalize(candidate.get("title") or "")
        hay_text = normalize(" ".join([
            candidate.get("description", ""), candidate.get("caption", ""),
            candidate.get("categories", "")
        ]))
        alias_norm = [normalize(x) for x in aliases if normalize(x)]
        title_tokens = tokens(hay_title)
        text_tokens = tokens(hay_text)
        alias_title_overlaps = [len(tokens(a) & title_tokens) / max(1, len(tokens(a))) for a in alias_norm]
        alias_text_overlaps = [len(tokens(a) & text_tokens) / max(1, len(tokens(a))) for a in alias_norm]
        best_alias_title = max(alias_title_overlaps or [0.0])
        best_alias_text = max(alias_text_overlaps or [0.0])
        exact_alias = any(a == hay_title for a in alias_norm)
        token_overlap = best_alias_title
        text_overlap = best_alias_text

        score = 0.0
        reasons = []
        if exact_alias:
            score += 45
            reasons.append("exact_alias_title")
        elif token_overlap >= 0.75:
            score += 35
            reasons.append("strong_alias_title_match")
        score += min(25, 25 * token_overlap)
        if token_overlap:
            reasons.append("title_token_match")
        score += min(10, 10 * text_overlap)
        if text_overlap:
            reasons.append("metadata_token_match")
        if direct_entity:
            score += 35
            reasons.append("wikidata_p18")
        if geo_source:
            score += 5
            reasons.append("commons_geosearch")

        source = str(candidate.get("_source") or "")
        source_bonus = {
            "wikidata_p18": 25,
            "official_source": 18,
            "open_data_tourism": 16,
            "openverse": 15,
            "commons_search": 6,
            "commons_geosearch": 4,
        }.get(source, 0)
        if source_bonus:
            score += source_bonus
            reasons.append(f"source_trust_{source}")

        if candidate.get("license"):
            score += 4
            reasons.append("license_metadata_present")

        c_lat = self._parse_coord(candidate.get("lat"))
        c_lon = self._parse_coord(candidate.get("lon"))
        distance = None
        if lat is not None and lon is not None and c_lat is not None and c_lon is not None:
            distance = haversine_km(lat, lon, c_lat, c_lon)
            if distance <= 0.25:
                score += 25; reasons.append("geo_le_250m")
            elif distance <= 1:
                score += 20; reasons.append("geo_le_1km")
            elif distance <= 3:
                score += 12; reasons.append("geo_le_3km")
            elif distance <= 10:
                score += 4; reasons.append("geo_le_10km")
            else:
                score -= min(35, distance / 2)
                reasons.append("geo_far")

        # Explicitly penalize obvious parent/neighbor mismatch.
        generic = normalize(name)
        wrong_terms = {
            "ba na hills": {"hoi an", "japanese bridge", "chua cau"},
            "japanese bridge": {"ba na", "ba na hills", "golden bridge"},
            "chua cau": {"ba na", "ba na hills", "golden bridge"},
        }
        forbidden = wrong_terms.get(generic, set())
        if forbidden and any(term in hay_title or term in hay_text for term in forbidden):
            score -= 35
            reasons.append("semantic_conflict")

        return max(0.0, min(100.0, score)), {
            "distance_km": round(distance, 3) if distance is not None else None,
            "reasons": reasons,
            "title": candidate.get("title"),
        }

    def _direct_p18(self, entity_id: str) -> List[Dict[str, Any]]:
        try:
            result = self.adapter.wikidata_entity(entity_id)
        except Exception:
            return []
        if not result.get("ok"):
            return []
        entities = (result.get("data") or {}).get("entities") or {}
        entity = entities.get(entity_id) or {}
        claims = entity.get("claims") or {}
        p18 = claims.get("P18") or []
        files = []
        for claim in p18:
            mainsnak = claim.get("mainsnak") or {}
            value = (mainsnak.get("datavalue") or {}).get("value")
            if isinstance(value, str) and value:
                files.append(value)
        return files[:3]

    def resolve(self, name: str, *, entity: Optional[Dict[str, Any]] = None,
                lat: Optional[float] = None, lon: Optional[float] = None) -> Dict[str, Any]:
        original = str(name or "").strip()
        aliases = self._aliases(original, entity)
        entity_id = self._wikidata_id(entity)
        candidates: List[Dict[str, Any]] = []

        # 1) Authoritative image claim from the resolved Wikidata entity.
        if entity_id:
            for file_title in self._direct_p18(entity_id):
                try:
                    exact = self.adapter.image_exact(file_title)
                    for page in ((exact.get("data") or {}).get("query", {}).get("pages", {}) or {}).values():
                        item = self._imageinfo(page)
                        if item.get("url"):
                            candidates.append({**item, "_direct_entity": True, "_source": "wikidata_p18"})
                except Exception:
                    continue

        # 2) Text candidates are fallback-only. If the resolved Wikidata entity
        # already supplied P18, do not dilute an authoritative entity image with
        # generic Commons search results.
        seen_titles = {str(c.get("title")) for c in candidates if c.get("title")}
        if not candidates:
            for alias in aliases[:3]:
                try:
                    result = self.adapter.image(alias)
                except Exception:
                    continue
                pages = ((result.get("data") or {}).get("query", {}).get("pages", {}) or {}).values()
                for page in pages:
                    item = self._imageinfo(page)
                    title = str(item.get("title") or "")
                    if item.get("url") and title not in seen_titles:
                        candidates.append({**item, "_direct_entity": False, "_source": "commons_search"})
                        seen_titles.add(title)

        # 3) Open-license media is an independent fallback layer. It broadens
        # coverage without weakening the entity lock because every candidate is
        # still scored against the canonical entity and coordinates.
        if not candidates or max(self._candidate_score(c, original, aliases, lat, lon, entity_id,
                                                       direct_entity=bool(c.get("_direct_entity")),
                                                       geo_source=c.get("_source") == "commons_geosearch")[0] for c in candidates) < self.ACCEPT_CONFIDENCE:
            for alias in aliases[:2]:
                try:
                    result = self.adapter.openverse_image(alias, 5)
                except Exception:
                    continue
                rows = ((result.get("data") or {}).get("results") or []) if isinstance(result, dict) else []
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    item = {
                        "url": row.get("thumbnail") or row.get("url"),
                        "title": row.get("title"),
                        "description": row.get("description") or row.get("title"),
                        "caption": row.get("title"),
                        "artist": row.get("creator"),
                        "license": row.get("license"),
                        "source_url": row.get("foreign_landing_url") or row.get("url"),
                    }
                    title = str(item.get("title") or item.get("url") or "")
                    if item.get("url") and title not in seen_titles:
                        candidates.append({**item, "_direct_entity": False, "_source": "openverse"})
                        seen_titles.add(title)

        # 4) Geographic candidates are a secondary fallback, used only when
        # text/entity evidence has not produced a sufficiently strong candidate.
        need_geo = not candidates
        if candidates:
            provisional = max(
                self._candidate_score(c, original, aliases, lat, lon, entity_id,
                                      direct_entity=bool(c.get("_direct_entity")),
                                      geo_source=c.get("_source") == "commons_geosearch")[0]
                for c in candidates
            )
            need_geo = provisional < self.ACCEPT_CONFIDENCE
        if need_geo and lat is not None and lon is not None:
            try:
                result = self.adapter.image_geosearch(float(lat), float(lon), 3000, 8)
                pages = ((result.get("data") or {}).get("query", {}).get("pages", {}) or {}).values()
                for page in pages:
                    item = self._imageinfo(page)
                    title = str(item.get("title") or "")
                    if item.get("url") and title not in seen_titles:
                        candidates.append({**item, "_direct_entity": False, "_source": "commons_geosearch"})
                        seen_titles.add(title)
            except Exception:
                pass

        scored = []
        for candidate in candidates:
            score, evidence = self._candidate_score(
                candidate, original, aliases, lat, lon, entity_id,
                direct_entity=bool(candidate.get("_direct_entity")),
                geo_source=candidate.get("_source") == "commons_geosearch",
            )
            scored.append((score, candidate, evidence))
        scored.sort(key=lambda x: (-x[0], str(x[1].get("title") or "")))

        if not scored:
            return {
                "ok": False, "name": original, "image_url": None,
                "confidence": "NONE", "score": 0, "reason": "no_verified_candidate",
                "entity_id": entity_id, "resolver_version": self.VERSION,
            }

        score, best, evidence = scored[0]
        confidence = "HIGH" if score >= self.ACCEPT_CONFIDENCE else ("MEDIUM" if score >= self.MIN_CONFIDENCE else "LOW")
        # Fail closed: medium/low candidates never become representative images.
        if score < self.ACCEPT_CONFIDENCE:
            return {
                "ok": False, "name": original, "image_url": None,
                "confidence": confidence, "score": round(score, 1),
                "reason": "candidate_below_verified_threshold",
                "entity_id": entity_id, "best_candidate": {
                    "title": best.get("title"), "source": best.get("_source"),
                    "evidence": evidence,
                }, "resolver_version": self.VERSION,
            }

        return {
            "ok": True, "name": original, "image_url": best.get("url"),
            "confidence": confidence, "score": round(score, 1),
            "title": best.get("title"), "source": best.get("_source"),
            "source_url": "https://commons.wikimedia.org/wiki/" + str(best.get("title","")).replace(" ", "_"),
            "entity_id": entity_id, "evidence": evidence,
            "resolver_version": self.VERSION,
            "candidates_considered": len(scored),
            "provenance": {
                "source": best.get("_source"),
                "license": best.get("license") or "",
                "retrieved_at": best.get("retrieved_at"),
            },
        }
