"""HDVIA Smart Knowledge Acquisition — Deep World Research.

Answer-time acquisition for any resolved tourism point. It searches several
public/open knowledge systems in parallel, builds topic-specific evidence, and
keeps all external evidence REFERENCE/CANDIDATE until governance validates it.
It never invents a missing fact and never treats a search hit as verified.
"""
from __future__ import annotations
import os, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from api_adapters import OpenAPIAdapter
from entity_resolution import EntityResolver
from image_entity_resolution import VerifiedImageResolver
from knowledge_quality import assess

VERSION = "1.30.1-hdv-giau-kinh-nghiem"

def _first(rows: Any) -> Dict[str, Any]:
    return rows[0] if isinstance(rows, list) and rows else {}

def _clean(text: Any, limit: int = 1800) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    return value[:limit]

def _unique(values: Iterable[str]) -> List[str]:
    out=[]; seen=set()
    for value in values:
        value=_clean(value, 300)
        key=value.casefold()
        if value and key not in seen:
            seen.add(key); out.append(value)
    return out

DOMAIN_ALIASES = {
    "history":"history", "lịch sử":"history",
    "culture":"culture", "văn hóa":"culture",
    "food":"food", "ẩm thực":"food", "đặc sản":"food", "món ăn":"food",
    "tourism":"tourism", "du lịch":"tourism", "điểm tham quan":"tourism", "địa danh":"landmarks",
    "landmarks":"landmarks", "landmark":"landmarks",
    "nature":"nature", "thiên nhiên":"nature",
    "people":"people", "con người":"people", "danh nhân":"people", "nhân vật":"people", "nhân vật lịch sử":"people",
    "economy":"economy", "kinh tế":"economy",
    "geography":"geography", "địa lý":"geography",
    "festival":"festival", "festivals":"festival", "lễ hội":"festival", "sự kiện":"festival",
}
TOPIC_QUERIES = {
    "history": ["{name} lịch sử", "{name} lịch sử hình thành", "{name} di tích lịch sử"],
    "culture": ["{name} văn hóa", "{name} phong tục truyền thống", "{name} di sản"],
    "food": ["{name} ẩm thực", "{name} món ăn đặc sản", "{name} đặc sản địa phương"],
    "tourism": ["{name} du lịch điểm tham quan", "{name} địa điểm nổi tiếng", "{name} trải nghiệm du lịch"],
    "landmarks": ["{name} danh thắng", "{name} địa danh nổi tiếng", "{name} điểm tham quan"],
    "nature": ["{name} thiên nhiên", "{name} cảnh quan", "{name} hệ sinh thái"],
    "people": ["{name} danh nhân", "{name} nhân vật lịch sử", "{name} nhân vật nổi tiếng"],
    "economy": ["{name} kinh tế", "{name} làng nghề sản xuất", "{name} sản phẩm địa phương"],
    "geography": ["{name} địa lý", "{name} vị trí địa lý", "{name} khí hậu"],
    "festival": ["{name} lễ hội", "{name} lễ hội truyền thống", "{name} sự kiện văn hóa"],
}
ALL_DOMAINS = tuple(TOPIC_QUERIES.keys())

class SmartKnowledgeAcquirer:
    VERSION = VERSION
    def __init__(self, adapter: Optional[OpenAPIAdapter] = None):
        self.adapter=adapter or OpenAPIAdapter()
        self.entity_resolver=EntityResolver(self.adapter)
        self.image_resolver=VerifiedImageResolver(self.adapter)

    def _wikipedia_topic(self, name: str, domain: str, lang: str) -> List[Dict[str, Any]]:
        rows=[]
        for q in TOPIC_QUERIES[domain][:2]:
            try:
                result=self.adapter.wikipedia(q.format(name=name), lang, 3)
                search=((result.get("data") or {}).get("query", {}).get("search") or []) if result.get("ok") else []
                for row in search[:3]:
                    title=row.get("title")
                    if not title: continue
                    page=self.adapter.wikipedia_page(title, lang=lang)
                    pdata=(page.get("data") or {}) if page.get("ok") else {}
                    extract=_clean(pdata.get("extract"), 1600)
                    if extract:
                        rows.append({"domain":domain,"title":title,"language":lang,"extract":extract,
                                     "source":f"Wikipedia {lang}","url":pdata.get("fullurl") or ""})
            except Exception:
                continue
        seen=set(); out=[]
        for row in rows:
            key=(row["title"],row["language"])
            if key not in seen:
                seen.add(key); out.append(row)
        return out[:4]

    def _wikidata_topic(self, name: str, domain: str) -> List[Dict[str, Any]]:
        rows=[]
        for q in TOPIC_QUERIES[domain][:2]:
            try:
                result=self.adapter.wikidata(q.format(name=name), 4)
                search=((result.get("data") or {}).get("search") or []) if result.get("ok") else []
                for row in search[:4]:
                    label=row.get("label") or row.get("title")
                    if label:
                        rows.append({"domain":domain,"id":row.get("id"),"label":label,
                                     "description":_clean(row.get("description"),500),"source":"Wikidata"})
            except Exception:
                continue
        seen=set(); out=[]
        for row in rows:
            key=str(row.get("id") or row.get("label"))
            if key not in seen:
                seen.add(key); out.append(row)
        return out[:5]

    def _web_topic(self, name: str, domain: str) -> List[Dict[str, Any]]:
        """Optional broad-web discovery through Google's official JSON API.
        Search-result HTML is never scraped; discovered pages remain candidates.
        """
        if not (os.getenv("GOOGLE_CSE_API_KEY") and os.getenv("GOOGLE_CSE_CX")):
            return []
        try:
            from data_acquisition import google_cse_search, fetch_url, extract_text, extract_title
            query=f'"{name}" {TOPIC_QUERIES[domain][0].format(name=name).replace(name, "")}'
            rows=google_cse_search(query, num=5)
        except Exception:
            return []
        out=[]
        for row in rows[:5]:
            url=row.get("url") or ""
            if not url: continue
            item={"domain":domain,"title":_clean(row.get("title"),240),"url":url,
                  "snippet":_clean(row.get("snippet"),700),"source":"Google CSE discovery","status":"CANDIDATE"}
            try:
                fetched=fetch_url(url, timeout=8, max_bytes=350000)
                text=_clean(extract_text(fetched),1400)
                if text:
                    item["page_title"]=_clean(extract_title(fetched.get("text","")),240)
                    item["extract"]=text
            except Exception:
                pass
            out.append(item)
        return out

    def acquire(self, target: str, *, include_live: bool=True, domains: Optional[List[str]]=None,
                question: str="", depth: str="bounded") -> Dict[str, Any]:
        name=_clean(target,240)
        if not name:
            return {"ok":False,"error":"missing_target","version":self.VERSION}
        entity=self.entity_resolver.resolve(name)
        geo=self.adapter.geocode(name) if include_live else {"ok":False}
        geo_rows=((geo.get("data") or {}).get("results") or []) if geo.get("ok") else []
        geo_row=_first(geo_rows)
        lat,lon=geo_row.get("latitude"),geo_row.get("longitude")
        requested=[]
        for raw in domains or []:
            key=DOMAIN_ALIASES.get(str(raw).strip().lower(), str(raw).strip().lower())
            if key in ALL_DOMAINS and key not in requested:
                requested.append(key)
        if str(depth).lower() in {"deep","full","world"}:
            selected=list(ALL_DOMAINS)
        else:
            selected=requested[:4] or ["history","culture","food","tourism"]
        for d in requested:
            if d not in selected: selected.insert(0,d)
        selected=selected[:10]

        blocks=[]; entities=[]; web_sources=[]
        with ThreadPoolExecutor(max_workers=min(8, max(1,len(selected)))) as pool:
            futures={}
            for domain in selected:
                futures[pool.submit(self._wikipedia_topic,name,domain,"vi")]=("wiki_vi",domain)
                futures[pool.submit(self._wikipedia_topic,name,domain,"en")]=("wiki_en",domain)
                futures[pool.submit(self._wikidata_topic,name,domain)]=("wikidata",domain)
                if os.getenv("GOOGLE_CSE_API_KEY") and os.getenv("GOOGLE_CSE_CX"):
                    futures[pool.submit(self._web_topic,name,domain)]=("web",domain)
            for future in as_completed(futures):
                kind,domain=futures[future]
                try: rows=future.result()
                except Exception: rows=[]
                if kind in ("wiki_vi", "wiki_en"): blocks.extend(rows)
                elif kind == "wikidata": entities.extend(rows)
                else: web_sources.extend(rows)

        by_domain={d:[] for d in selected}
        for b in blocks: by_domain.setdefault(b.get("domain"),[]).append(b)
        blocks=[]
        for d in selected:
            seen=set(); count=0
            for b in by_domain.get(d,[]):
                key=(b.get("title"),b.get("language"))
                if key in seen: continue
                seen.add(key); blocks.append(b); count += 1
                if count>=3: break

        osm=self.adapter.osm_search(name,8) if include_live else {"ok":False}
        osm_rows=(osm.get("data") or {}).get("results") or [] if osm.get("ok") else []
        image=self.image_resolver.resolve(name,entity=entity,lat=lat,lon=lon) if include_live else {"ok":False}

        sources=[]
        if entity.get("wikidata"): sources.append("Wikidata")
        sources.extend(sorted(set(("Wikipedia tiếng Việt" if b.get("source") == "Wikipedia vi" else "Wikipedia tiếng Anh" if b.get("source") == "Wikipedia en" else str(b.get("source"))) for b in blocks if b.get("source"))))
        if osm_rows: sources.append("OpenStreetMap")
        if image.get("ok"): sources.append(str(image.get("source") or "Wikimedia Commons"))
        if web_sources: sources.append("Google CSE discovery")
        sources=_unique(sources)
        assessments=[assess({"source":s,"source_type":"open"},sources) for s in sources]
        confidence="LOW"
        if len(sources)>=5 and entity.get("confidence") in {"HIGH","MEDIUM"}: confidence="HIGH"
        elif len(sources)>=2: confidence="MEDIUM"

        profile={
            "name":name,"canonical_name":entity.get("canonical_name",name),"entity_resolution":entity,
            "coordinates":{"lat":lat,"lon":lon} if lat is not None and lon is not None else None,
            "wikipedia":{
                "vi_extract":next((b["extract"] for b in blocks if b.get("language")=="vi" and b.get("domain")=="tourism"),""),
                "en_extract":next((b["extract"] for b in blocks if b.get("language")=="en" and b.get("domain")=="tourism"),""),
            },
            "knowledge_blocks":blocks,"related_entities":entities[:40],"web_sources":web_sources[:40],
            "osm":{"results":osm_rows[:8]},"representative_image":image if image.get("ok") else None,
            "source_count":len(sources),"sources":sources,"confidence":confidence,
            "source_assessments":assessments,
            "status":"REFERENCE" if confidence in {"HIGH","MEDIUM"} else "CANDIDATE",
            "research_depth":"DEEP" if str(depth).lower() in {"deep","full","world"} else "BOUNDED",
            "domains_researched":selected,
            "acquired_at":datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z"),
            "acquirer_version":self.VERSION,
        }
        return {"ok":True,"profile":profile}
